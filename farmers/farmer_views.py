import json
from decimal import Decimal
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db.models import Sum, Count, Max, Avg, Q
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone

from .models import FarmerProfile, Payout, FarmerNotificationSetting
from products.models import Product, Category, Review, ContactMessage
from orders.models import Order, OrderItem
from accounts.models import User, Conversation, Message
from notifications.models import Notification

from .forms import (
    FarmerProfileForm, ProductForm, PayoutRequestForm,
    FarmerNotificationSettingsForm, SupportForm
)

def farmer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.account_type != 'FARMER':
            messages.error(request, "Access denied. Only registered farmers can access the Farmer Dashboard.")
            return redirect('dashboard')
        if not hasattr(request.user, 'farmer_profile'):
            messages.error(request, "Farmer Profile not found. Please contact support.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

def get_farmer_context(request):
    profile = request.user.farmer_profile
    
    # Unread incoming messages count
    unread_messages_count = Message.objects.filter(
        conversation__farmer=profile,
        is_read=False
    ).exclude(sender=request.user).count()
    
    # Pending orders count
    pending_orders_count = OrderItem.objects.filter(
        farmer=profile,
        order__status='PENDING'
    ).values('order').distinct().count()
    
    # Unread notifications count
    unread_notifications_count = Notification.objects.filter(
        buyer=request.user,
        is_read=False
    ).count()
    
    return {
        'farmer_profile': profile,
        'unread_messages_count': unread_messages_count,
        'pending_orders_count': pending_orders_count,
        'unread_notifications_count': unread_notifications_count,
    }

@login_required
@farmer_required
def farmer_dashboard(request):
    user = request.user
    profile = user.farmer_profile
    context = get_farmer_context(request)
    
    # Basic Metrics
    total_sales = OrderItem.objects.filter(
        farmer=profile,
        order__status='DELIVERED'
    ).aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
    
    total_orders = OrderItem.objects.filter(
        farmer=profile
    ).values('order').distinct().count()
    
    active_products = Product.objects.filter(
        farmer=profile,
        is_available=True
    ).count()
    
    total_customers = OrderItem.objects.filter(
        farmer=profile
    ).values('order__user').distinct().count()
    
    pending_orders = OrderItem.objects.filter(
        farmer=profile,
        order__status='PENDING'
    ).values('order').distinct().count()
    
    # Percentage growth placeholder calculations (compare past 7 days)
    # Replicated metrics logic
    sales_growth = "+ 14.5%"
    orders_growth = "+ 8.2%"
    
    # Recent orders containing this farmer's products
    order_ids = OrderItem.objects.filter(farmer=profile).values_list('order_id', flat=True).distinct()
    recent_orders = Order.objects.filter(id__in=order_ids).order_by('-created_at')[:5]
    
    # Format orders to include farmer's portion only
    formatted_recent_orders = []
    for order in recent_orders:
        farmer_portion = OrderItem.objects.filter(order=order, farmer=profile).aggregate(tot=Sum('subtotal'))['tot'] or Decimal('0.00')
        formatted_recent_orders.append({
            'order_number': order.order_number,
            'full_name': order.full_name,
            'created_at': order.created_at,
            'amount': farmer_portion,
            'status': order.status
        })
        
    # Top Selling Products
    top_selling = OrderItem.objects.filter(
        farmer=profile,
        order__status='DELIVERED'
    ).values(
        'product__id', 'product__name', 'product__main_image', 'product__slug', 'product__unit'
    ).annotate(
        qty_sold=Sum('quantity'),
        revenue=Sum('subtotal')
    ).order_by('-qty_sold')[:5]
    
    # Financial Payout math
    completed_earnings = total_sales
    completed_payouts = Payout.objects.filter(farmer=profile, status='COMPLETED').aggregate(sum_amt=Sum('amount'))['sum_amt'] or Decimal('0.00')
    pending_payouts = Payout.objects.filter(farmer=profile, status='PENDING').aggregate(sum_amt=Sum('amount'))['sum_amt'] or Decimal('0.00')
    available_balance = completed_earnings - completed_payouts - pending_payouts
    
    # Chart.js Sales data (past 7 days)
    today = timezone.localdate()
    days = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
    chart_labels = [d.strftime('%a') for d in days]
    chart_values = []
    for d in days:
        sales_day = OrderItem.objects.filter(
            farmer=profile,
            order__status='DELIVERED',
            order__created_at__date=d
        ).aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
        chart_values.append(float(sales_day))
        
    context.update({
        'total_sales': total_sales,
        'total_orders': total_orders,
        'active_products': active_products,
        'total_customers': total_customers,
        'pending_orders': pending_orders,
        'sales_growth': sales_growth,
        'orders_growth': orders_growth,
        'recent_orders': formatted_recent_orders,
        'top_selling': top_selling,
        'available_balance': available_balance,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
    })
    return render(request, 'farmer/dashboard.html', context)

@login_required
@farmer_required
def farmer_products(request):
    profile = request.user.farmer_profile
    context = get_farmer_context(request)
    
    # Query products
    products_qs = Product.objects.filter(farmer=profile).select_related('category').order_by('-created_at')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        products_qs = products_qs.filter(
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        
    # Filters
    category_filter = request.GET.get('category', '')
    if category_filter:
        products_qs = products_qs.filter(category__slug=category_filter)
        
    status_filter = request.GET.get('status', '')
    if status_filter:
        if status_filter == 'active':
            products_qs = products_qs.filter(is_available=True, stock_quantity__gt=0)
        elif status_filter == 'outofstock':
            products_qs = products_qs.filter(stock_quantity=0)
        elif status_filter == 'inactive':
            products_qs = products_qs.filter(is_available=False)
            
    # Pagination
    paginator = Paginator(products_qs, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context.update({
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_filter,
        'selected_status': status_filter,
    })
    return render(request, 'farmer/products.html', context)

@login_required
@farmer_required
def farmer_add_product(request):
    profile = request.user.farmer_profile
    context = get_farmer_context(request)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.farmer = profile
            product.save()
            # Handle multiple uploaded images
            images = request.FILES.getlist('images')
            from products.models import ProductImage
            if images:
                # If no main_image was provided, set the first uploaded as main
                if not product.main_image:
                    product.main_image = images[0]
                    product.save()
                for idx, img in enumerate(images):
                    ProductImage.objects.create(product=product, image=img, order=idx)
            messages.success(request, f"Product '{product.name}' added successfully!")
            return redirect('farmer_products')
        else:
            messages.error(request, "Failed to add product. Please verify forms input.")
    else:
        form = ProductForm()
        
    context.update({
        'form': form,
    })
    return render(request, 'farmer/add_product.html', context)

@login_required
@farmer_required
def farmer_edit_product(request, slug):
    profile = request.user.farmer_profile
    product = get_object_or_404(Product, slug=slug, farmer=profile)
    context = get_farmer_context(request)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            # Handle additional uploaded images on edit
            images = request.FILES.getlist('images')
            from products.models import ProductImage
            if images:
                if not product.main_image:
                    product.main_image = images[0]
                    product.save()
                for idx, img in enumerate(images):
                    ProductImage.objects.create(product=product, image=img, order=idx)
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('farmer_products')
        else:
            messages.error(request, "Failed to update product.")
    else:
        form = ProductForm(instance=product)
        
    context.update({
        'form': form,
        'product': product,
    })
    return render(request, 'farmer/edit_product.html', context)

@login_required
@farmer_required
def farmer_delete_product(request, slug):
    profile = request.user.farmer_profile
    product = get_object_or_404(Product, slug=slug, farmer=profile)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f"Product '{product_name}' deleted successfully.")
        return redirect('farmer_products')
        
    context = get_farmer_context(request)
    context.update({'product': product})
    return render(request, 'farmer/delete_product_confirm.html', context)

@login_required
@farmer_required
def farmer_orders(request):
    profile = request.user.farmer_profile
    context = get_farmer_context(request)
    
    # Filter order items matching this farmer
    status_filter = request.GET.get('status', 'all').upper()
    order_items = OrderItem.objects.filter(farmer=profile).select_related('order', 'product')
    
    if status_filter != 'ALL':
        order_items = order_items.filter(order__status=status_filter)
        
    # Group orders
    orders_dict = {}
    for item in order_items:
        o = item.order
        if o.order_number not in orders_dict:
            orders_dict[o.order_number] = {
                'order': o,
                'items_count': 0,
                'total_amount': Decimal('0.00'),
                'status': o.status,
                'created_at': o.created_at,
                'full_name': o.full_name,
            }
        orders_dict[o.order_number]['items_count'] += item.quantity
        orders_dict[o.order_number]['total_amount'] += item.subtotal
        
    # Paginate grouped list
    grouped_list = sorted(orders_dict.values(), key=lambda x: x['created_at'], reverse=True)
    paginator = Paginator(grouped_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context.update({
        'page_obj': page_obj,
        'selected_status': status_filter,
    })
    return render(request, 'farmer/orders.html', context)

@login_required
@farmer_required
def farmer_order_detail(request, order_number):
    profile = request.user.farmer_profile
    order = get_object_or_404(Order, order_number=order_number)
    context = get_farmer_context(request)
    
    # Filter items specific to this farmer
    items = OrderItem.objects.filter(order=order, farmer=profile).select_related('product')
    if not items.exists():
        messages.error(request, "Access denied. Order details do not contain your farm products.")
        return redirect('farmer_orders')
        
    # Calculate totals for this farmer's share
    subtotal = items.aggregate(tot=Sum('subtotal'))['tot'] or Decimal('0.00')
    delivery_fee = order.delivery_fee
    total = subtotal + delivery_fee
    
    if request.method == 'POST':
        action = request.POST.get('action')
        # Valid state machine transitions
        current_status = order.status
        next_status = None
        
        if action == 'accept' and current_status == 'PENDING':
            next_status = 'PROCESSING'
            msg = "Your order has been accepted and is being processed."
        elif action == 'reject' and current_status == 'PENDING':
            next_status = 'CANCELLED'
            msg = "Your order has been rejected due to stock issues."
        elif action == 'mark_ready' and current_status == 'PROCESSING':
            next_status = 'SHIPPED' # Represents Shipped in system choices
            msg = "Your order has been dispatched and is on its way."
        elif action == 'mark_delivered' and current_status == 'SHIPPED':
            next_status = 'DELIVERED'
            msg = "Your order has been successfully delivered."
        elif action == 'mark_paid':
            order.payment_status = 'PAID'
            order.save()
            messages.success(request, "Order payment status marked as PAID!")
            return redirect('farmer_order_detail', order_number=order.order_number)
        elif action == 'mark_unpaid':
            order.payment_status = 'UNPAID'
            order.save()
            messages.success(request, "Order payment status marked as UNPAID!")
            return redirect('farmer_order_detail', order_number=order.order_number)
            
        if next_status:
            order.status = next_status
            order.save()
            
            # Send notification to the buyer
            Notification.objects.create(
                buyer=order.user,
                title=f"Order Status Update: {order.order_number}",
                message=f"Status: {order.get_status_display()}. {msg}",
                notification_type='ORDER_UPDATE'
            )
            
            messages.success(request, f"Order status updated to {order.get_status_display()} successfully!")
            return redirect('farmer_order_detail', order_number=order.order_number)
        else:
            messages.error(request, "Invalid status transition action.")
            
    context.update({
        'order': order,
        'items': items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
    })
    return render(request, 'farmer/order_detail.html', context)

@login_required
@farmer_required
def farmer_earnings(request):
    profile = request.user.farmer_profile
    context = get_farmer_context(request)
    
    # Calculations
    total_sales = OrderItem.objects.filter(
        farmer=profile,
        order__status='DELIVERED'
    ).aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
    
    completed_payouts = Payout.objects.filter(farmer=profile, status='COMPLETED').aggregate(sum_amt=Sum('amount'))['sum_amt'] or Decimal('0.00')
    pending_payouts = Payout.objects.filter(farmer=profile, status='PENDING').aggregate(sum_amt=Sum('amount'))['sum_amt'] or Decimal('0.00')
    available_balance = total_sales - completed_payouts - pending_payouts
    
    # Monthly / Weekly sales totals
    today = timezone.localdate()
    start_of_month = today.replace(day=1)
    start_of_week = today - datetime.timedelta(days=today.weekday())
    
    sales_month = OrderItem.objects.filter(
        farmer=profile,
        order__status='DELIVERED',
        order__created_at__date__gte=start_of_month
    ).aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
    
    sales_week = OrderItem.objects.filter(
        farmer=profile,
        order__status='DELIVERED',
        order__created_at__date__gte=start_of_week
    ).aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
    
    # Chart: Earnings by category
    category_sales = OrderItem.objects.filter(
        farmer=profile,
        order__status='DELIVERED'
    ).values('product__category__name').annotate(sales=Sum('subtotal')).order_by('-sales')
    
    pie_labels = [item['product__category__name'] or 'Produce' for item in category_sales]
    pie_values = [float(item['sales']) for item in category_sales]
    
    # Chart: Earnings overview (last 6 months)
    months_labels = []
    months_values = []
    for i in range(5, -1, -1):
        target_month = (today.month - i - 1) % 12 + 1
        target_year = today.year if today.month - i > 0 else today.year - 1
        sales_m = OrderItem.objects.filter(
            farmer=profile,
            order__status='DELIVERED',
            order__created_at__month=target_month,
            order__created_at__year=target_year
        ).aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
        months_labels.append(datetime.date(target_year, target_month, 1).strftime('%B'))
        months_values.append(float(sales_m))
        
    # Transaction history (delivered items)
    transactions_list = OrderItem.objects.filter(
        farmer=profile,
        order__status='DELIVERED'
    ).select_related('order').order_by('-order__created_at')
    
    paginator = Paginator(transactions_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context.update({
        'total_sales': total_sales,
        'available_balance': available_balance,
        'pending_payouts': pending_payouts,
        'sales_month': sales_month,
        'sales_week': sales_week,
        'pie_labels': json.dumps(pie_labels),
        'pie_values': json.dumps(pie_values),
        'months_labels': json.dumps(months_labels),
        'months_values': json.dumps(months_values),
        'page_obj': page_obj,
    })
    return render(request, 'farmer/earnings.html', context)

@login_required
@farmer_required
def farmer_payouts(request):
    profile = request.user.farmer_profile
    context = get_farmer_context(request)
    
    # Calculate Balance
    total_sales = OrderItem.objects.filter(
        farmer=profile,
        order__status='DELIVERED'
    ).aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
    
    completed_payouts = Payout.objects.filter(farmer=profile, status='COMPLETED').aggregate(sum_amt=Sum('amount'))['sum_amt'] or Decimal('0.00')
    pending_payouts = Payout.objects.filter(farmer=profile, status='PENDING').aggregate(sum_amt=Sum('amount'))['sum_amt'] or Decimal('0.00')
    available_balance = total_sales - completed_payouts - pending_payouts
    
    if request.method == 'POST':
        form = PayoutRequestForm(request.POST)
        if form.is_valid():
            payout_amount = form.cleaned_data['amount']
            if payout_amount > available_balance:
                form.add_error('amount', f"Insufficient balance. Available payout is GHS {available_balance:.2f}")
            else:
                payout = form.save(commit=False)
                payout.farmer = profile
                payout.status = 'PENDING'
                payout.save()
                messages.success(request, f"Payout request of GHS {payout_amount:.2f} submitted successfully!")
                return redirect('farmer_payouts')
        else:
            messages.error(request, "Failed to submit payout request. Please verify inputs.")
    else:
        form = PayoutRequestForm()
        
    payouts_history = Payout.objects.filter(farmer=profile).order_by('-requested_at')
    
    context.update({
        'available_balance': available_balance,
        'form': form,
        'payouts_history': payouts_history,
    })
    return render(request, 'farmer/payouts.html', context)

@login_required
@farmer_required
def farmer_customers(request):
    profile = request.user.farmer_profile
    context = get_farmer_context(request)
    
    # Calculate buyer stats dynamically
    customers_qs = OrderItem.objects.filter(
        farmer=profile
    ).values(
        'order__user_id', 'order__user__username', 'order__user__first_name', 'order__user__last_name'
    ).annotate(
        orders_count=Count('order', distinct=True),
        total_spent=Sum('subtotal'),
        last_order_date=Max('order__created_at')
    ).order_by('-total_spent')
    
    paginator = Paginator(customers_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context.update({
        'page_obj': page_obj,
    })
    return render(request, 'farmer/customers.html', context)

@login_required
@farmer_required
def farmer_customer_detail(request, user_id):
    profile = request.user.farmer_profile
    buyer = get_object_or_404(User, id=user_id)
    context = get_farmer_context(request)
    
    # Order items from this buyer specific to this farmer
    items = OrderItem.objects.filter(farmer=profile, order__user=buyer).select_related('order', 'product').order_by('-order__created_at')
    
    if not items.exists():
        messages.error(request, "Access denied. Buyer has not purchased products from your farm.")
        return redirect('farmer_customers')
        
    total_spent = items.aggregate(tot=Sum('subtotal'))['tot'] or Decimal('0.00')
    orders_count = items.values('order').distinct().count()
    last_order = items.first().order
    
    context.update({
        'buyer': buyer,
        'items': items,
        'total_spent': total_spent,
        'orders_count': orders_count,
        'last_order': last_order,
    })
    return render(request, 'farmer/customer_detail.html', context)

@login_required
@farmer_required
def farmer_messages(request):
    profile = request.user.farmer_profile
    context = get_farmer_context(request)
    
    # Conversations specific to this farmer
    conversations = Conversation.objects.filter(farmer=profile).select_related('buyer').order_by('-updated_at')
    
    active_conv_id = request.GET.get('conv')
    active_conversation = None
    messages_list = []
    
    if active_conv_id:
        active_conversation = get_object_or_404(Conversation, id=active_conv_id, farmer=profile)
        # Mark incoming messages as read
        Message.objects.filter(conversation=active_conversation, is_read=False).exclude(sender=request.user).update(is_read=True)
        messages_list = active_conversation.messages.all().order_by('created_at')
    elif conversations.exists():
        # Load the latest conversation as default
        active_conversation = conversations.first()
        Message.objects.filter(conversation=active_conversation, is_read=False).exclude(sender=request.user).update(is_read=True)
        messages_list = active_conversation.messages.all().order_by('created_at')
        
    if request.method == 'POST' and active_conversation:
        msg_text = request.POST.get('message_text')
        if msg_text:
            Message.objects.create(
                conversation=active_conversation,
                sender=request.user,
                message=msg_text
            )
            active_conversation.save() # Updates updated_at timestamp
            return redirect(f"/farmer/messages/?conv={active_conversation.id}")
            
    context.update({
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages_list': messages_list,
    })
    return render(request, 'farmer/messages.html', context)

@login_required
@farmer_required
def farmer_reviews(request):
    profile = request.user.farmer_profile
    context = get_farmer_context(request)
    
    reviews_qs = Review.objects.filter(product__farmer=profile).select_related('buyer', 'product').order_by('-created_at')
    
    # Average rating calculations
    avg_rating = reviews_qs.aggregate(avg=Avg('rating'))['avg'] or 4.5
    total_reviews = reviews_qs.count()
    
    # Rating count breakdown
    rating_breakdown = {}
    for score in range(1, 6):
        count = reviews_qs.filter(rating=score).count()
        percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
        rating_breakdown[score] = {
            'count': count,
            'percentage': round(percentage, 1)
        }
        
    # Top rated products
    top_rated_products = Product.objects.filter(farmer=profile, review_count__gt=0).order_by('-rating')[:3]
    
    context.update({
        'reviews': reviews_qs,
        'avg_rating': round(avg_rating, 2),
        'total_reviews': total_reviews,
        'rating_breakdown': rating_breakdown,
        'top_rated_products': top_rated_products,
    })
    return render(request, 'farmer/reviews.html', context)

@login_required
@farmer_required
def farmer_profile(request):
    profile = request.user.farmer_profile
    context = get_farmer_context(request)
    
    if request.method == 'POST':
        form = FarmerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Farm Profile updated successfully!")
            return redirect('farmer_profile')
        else:
            messages.error(request, "Failed to update Farm Profile. Check input fields.")
    else:
        form = FarmerProfileForm(instance=profile)
        
    context.update({
        'form': form,
    })
    return render(request, 'farmer/profile.html', context)

@login_required
@farmer_required
def farmer_settings(request):
    profile = request.user.farmer_profile
    context = get_farmer_context(request)
    
    # Ensure notification settings object exists
    notif_settings, created = FarmerNotificationSetting.objects.get_or_create(farmer=profile)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'notifications':
            form_notif = FarmerNotificationSettingsForm(request.POST, instance=notif_settings)
            if form_notif.is_valid():
                form_notif.save()
                messages.success(request, "Notification settings updated successfully.")
                return redirect('farmer_settings')
            else:
                messages.error(request, "Failed to update notification settings.")
                
        elif action == 'change_password':
            form_pwd = PasswordChangeForm(request.user, request.POST)
            if form_pwd.is_valid():
                user = form_pwd.save()
                update_session_auth_hash(request, user) # Keeps user logged in
                messages.success(request, "Your password has been changed successfully.")
                return redirect('farmer_settings')
            else:
                messages.error(request, "Password change failed. Check fields.")
                
        elif action == 'delete_account':
            user = request.user
            user.delete()
            messages.success(request, "Your farm account has been successfully deleted.")
            return redirect('home')
            
    form_notif = FarmerNotificationSettingsForm(instance=notif_settings)
    form_pwd = PasswordChangeForm(request.user)
    
    context.update({
        'form_notif': form_notif,
        'form_pwd': form_pwd,
    })
    return render(request, 'farmer/settings.html', context)

@login_required
@farmer_required
def farmer_notifications(request):
    context = get_farmer_context(request)
    
    # Retrieve user's system notifications (using generic recipient field buyer)
    notifications_list = Notification.objects.filter(buyer=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notif_id = request.POST.get('notification_id')
        
        if action == 'mark_read' and notif_id:
            notif = get_object_or_404(Notification, id=notif_id, buyer=request.user)
            notif.is_read = True
            notif.save()
            return JsonResponse({'status': 'success'})
            
        elif action == 'mark_all_read':
            Notification.objects.filter(buyer=request.user, is_read=False).update(is_read=True)
            messages.success(request, "All notifications marked as read.")
            return redirect('farmer_notifications')
            
    context.update({
        'notifications': notifications_list,
    })
    return render(request, 'farmer/notifications.html', context)

@login_required
@farmer_required
def farmer_support(request):
    context = get_farmer_context(request)
    
    if request.method == 'POST':
        form = SupportForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your support message has been sent successfully. We will get back to you shortly.")
            return redirect('farmer_support')
        else:
            messages.error(request, "Failed to submit support request. Verify fields.")
    else:
        form = SupportForm(initial={
            'full_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'phone': request.user.phone or request.user.farmer_profile.phone
        })
        
    context.update({
        'form': form,
    })
    return render(request, 'farmer/support.html', context)
