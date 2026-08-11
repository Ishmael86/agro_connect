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

from django.contrib.auth import get_user_model
from farmers.models import FarmerProfile, Payout
from products.models import Product, Category, Review, ContactMessage
from orders.models import Order, OrderItem
from accounts.models import Conversation, Message
from notifications.models import Notification

from .models import ActivityLog, SupportTicket, SupportTicketMessage, Promotion, SiteSettings
from .forms import (
    AdminUserForm, CategoryForm, OrderStatusForm,
    PromotionForm, SettingsForm, SupportTicketReplyForm, AdminProfileForm
)

User = get_user_model()

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Access denied. Administrative privileges required.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def log_admin_action(request, action):
    ActivityLog.objects.create(
        admin=request.user,
        action=action,
        ip_address=request.META.get('REMOTE_ADDR')
    )

def get_admin_context(request):
    open_tickets = SupportTicket.objects.filter(status='OPEN').count()
    pending_payouts = Payout.objects.filter(status='PENDING').count()
    pending_farmers = FarmerProfile.objects.filter(verified=False).count()
    
    # Unread notifications for admin user
    unread_notifications = Notification.objects.filter(buyer=request.user, is_read=False).count()
    
    return {
        'open_tickets_count': open_tickets,
        'pending_payouts_count': pending_payouts,
        'pending_farmers_count': pending_farmers,
        'unread_notifications_count': unread_notifications,
    }

@login_required
@admin_required
def admin_dashboard(request):
    context = get_admin_context(request)
    
    # 1. KPI Statistics
    total_users = User.objects.filter(is_superuser=False, is_staff=False).count()
    total_farmers = FarmerProfile.objects.count()
    total_buyers = User.objects.filter(account_type='BUYER').count()
    total_sales = OrderItem.objects.filter(order__status='DELIVERED').aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='PENDING').count()
    total_products = Product.objects.count()
    total_reviews = Review.objects.count()
    support_tickets = SupportTicket.objects.count()
    
    # Growth rates placeholders (compared to past 7 days)
    sales_growth = "+12.5%"
    users_growth = "+8.3%"
    orders_growth = "+15.3%"
    pending_growth = "-4.2%"
    
    # 2. Charts Data
    # Sales Overview (past 7 days)
    today = timezone.localdate()
    days = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
    chart_labels = [d.strftime('%a') for d in days]
    chart_values = []
    for d in days:
        sales_day = OrderItem.objects.filter(
            order__status='DELIVERED',
            order__created_at__date=d
        ).aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
        chart_values.append(float(sales_day))
        
    # Orders Overview doughnut (Delivered, Processing, Pending, Cancelled)
    order_delivered = Order.objects.filter(status='DELIVERED').count()
    order_processing = Order.objects.filter(status='PROCESSING').count()
    order_pending = Order.objects.filter(status='PENDING').count()
    order_cancelled = Order.objects.filter(status='CANCELLED').count()
    order_status_values = [order_delivered, order_processing, order_pending, order_cancelled]
    
    # Top categories revenue splits
    cat_sales = OrderItem.objects.filter(order__status='DELIVERED').values('product__category__name').annotate(sales=Sum('subtotal')).order_by('-sales')
    top_categories = []
    grand_sales = sum(float(item['sales']) for item in cat_sales) if cat_sales else 1
    
    for item in cat_sales[:5]:
        rev = float(item['sales'])
        pct = (rev / grand_sales * 100) if grand_sales > 0 else 0
        top_categories.append({
            'name': item['product__category__name'] or 'Produce',
            'revenue': rev,
            'percentage': round(pct, 1)
        })
        
    # Recent Orders List
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    formatted_recent_orders = []
    for ord in recent_orders:
        farmer_item = OrderItem.objects.filter(order=ord).first()
        farm_name = farmer_item.farmer.farm_name if farmer_item and farmer_item.farmer else "AgroConnect"
        formatted_recent_orders.append({
            'order': ord,
            'farm_name': farm_name
        })
        
    # Platform Summary metrics
    active_products = Product.objects.filter(is_available=True).count()
    total_categories = Category.objects.count()
    
    context.update({
        'total_users': total_users,
        'total_farmers': total_farmers,
        'total_buyers': total_buyers,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_products': total_products,
        'total_reviews': total_reviews,
        'support_tickets': support_tickets,
        
        'sales_growth': sales_growth,
        'users_growth': users_growth,
        'orders_growth': orders_growth,
        'pending_growth': pending_growth,
        
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'order_status_values': json.dumps(order_status_values),
        
        'top_categories': top_categories,
        'recent_orders': formatted_recent_orders,
        
        'active_products': active_products,
        'total_categories': total_categories,
    })
    
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@admin_required
def admin_users(request):
    context = get_admin_context(request)
    
    # Query all users excluding superusers and admin staff
    users_qs = User.objects.filter(is_superuser=False, is_staff=False).order_by('-date_joined')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users_qs = users_qs.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
        
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users_qs = users_qs.filter(account_type=role_filter)
        
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        if status_filter == 'active':
            users_qs = users_qs.filter(is_active=True)
        elif status_filter == 'inactive':
            users_qs = users_qs.filter(is_active=False)
            
    # Pagination
    paginator = Paginator(users_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context.update({
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_role': role_filter,
        'selected_status': status_filter,
    })
    return render(request, 'admin_panel/users.html', context)

@login_required
@admin_required
def admin_user_detail(request, id):
    context = get_admin_context(request)
    user_item = get_object_or_404(User, id=id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_status':
            user_item.is_active = not user_item.is_active
            user_item.save()
            log_admin_action(request, f"Toggled status of user {user_item.username} to {user_item.is_active}")
            messages.success(request, f"User status updated successfully.")
            return redirect('admin_user_detail', id=user_item.id)
            
        elif action == 'delete_user':
            username = user_item.username
            user_item.delete()
            log_admin_action(request, f"Deleted user account {username}")
            messages.success(request, f"User account '{username}' deleted successfully.")
            return redirect('admin_users')
            
    form = AdminUserForm(instance=user_item)
    context.update({
        'user_item': user_item,
        'form': form,
    })
    return render(request, 'admin_panel/user_detail.html', context)

@login_required
@admin_required
def admin_farmers(request):
    context = get_admin_context(request)
    farmers_qs = FarmerProfile.objects.all().order_by('-created_at')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        farmers_qs = farmers_qs.filter(
            Q(farm_name__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(location__icontains=search_query)
        )
        
    # Filters
    status_filter = request.GET.get('status', '')
    if status_filter:
        if status_filter == 'verified':
            farmers_qs = farmers_qs.filter(verified=True)
        elif status_filter == 'pending':
            farmers_qs = farmers_qs.filter(verified=False)
            
    paginator = Paginator(farmers_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate crop & sales statistics for listing
    farmers_list = []
    for profile in page_obj:
        crops_count = profile.products.count()
        sales_sum = OrderItem.objects.filter(farmer=profile, order__status='DELIVERED').aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
        farmers_list.append({
            'profile': profile,
            'crops_count': crops_count,
            'sales_sum': sales_sum
        })
        
    context.update({
        'page_obj': page_obj,
        'farmers_list': farmers_list,
        'search_query': search_query,
        'selected_status': status_filter,
    })
    return render(request, 'admin_panel/farmers.html', context)

@login_required
@admin_required
def admin_farmer_detail(request, id):
    context = get_admin_context(request)
    profile = get_object_or_404(FarmerProfile, id=id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'verify_farmer':
            profile.verified = True
            profile.save()
            log_admin_action(request, f"Verified farmer profile for {profile.farm_name}")
            messages.success(request, f"Farmer profile '{profile.farm_name}' verified successfully.")
            
            # Send notification
            Notification.objects.create(
                buyer=profile.user,
                title="Profile Verified!",
                message="Your AgroConnect farmer profile has been verified successfully.",
                notification_type='PROMOTION'
            )
            return redirect('admin_farmer_detail', id=profile.id)
            
        elif action == 'reject_farmer':
            profile.verified = False
            profile.save()
            log_admin_action(request, f"Revoked verification for {profile.farm_name}")
            messages.warning(request, f"Farmer verification revoked.")
            return redirect('admin_farmer_detail', id=profile.id)
            
    crops = profile.products.all().select_related('category')
    sales_total = OrderItem.objects.filter(farmer=profile, order__status='DELIVERED').aggregate(tot=Sum('subtotal'))['tot'] or Decimal('0.00')
    orders_count = OrderItem.objects.filter(farmer=profile).values('order').distinct().count()
    
    context.update({
        'profile': profile,
        'crops': crops,
        'sales_total': sales_total,
        'orders_count': orders_count,
    })
    return render(request, 'admin_panel/farmer_detail.html', context)

@login_required
@admin_required
def admin_buyers(request):
    context = get_admin_context(request)
    buyers_qs = User.objects.filter(account_type='BUYER').order_by('-date_joined')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        buyers_qs = buyers_qs.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
        
    paginator = Paginator(buyers_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    buyers_list = []
    for buyer in page_obj:
        ord_count = buyer.orders.count()
        total_spent = buyer.orders.filter(status='DELIVERED').aggregate(tot=Sum('total'))['tot'] or Decimal('0.00')
        buyers_list.append({
            'buyer': buyer,
            'ord_count': ord_count,
            'total_spent': total_spent
        })
        
    context.update({
        'page_obj': page_obj,
        'buyers_list': buyers_list,
        'search_query': search_query,
    })
    return render(request, 'admin_panel/buyers.html', context)

@login_required
@admin_required
def admin_buyer_detail(request, id):
    context = get_admin_context(request)
    buyer = get_object_or_404(User, id=id, account_type='BUYER')
    
    orders = buyer.orders.all().order_by('-created_at')
    total_spent = orders.filter(status='DELIVERED').aggregate(tot=Sum('total'))['tot'] or Decimal('0.00')
    reviews_count = buyer.product_reviews.count()
    
    context.update({
        'buyer': buyer,
        'orders': orders,
        'total_spent': total_spent,
        'reviews_count': reviews_count,
    })
    return render(request, 'admin_panel/buyer_detail.html', context)

@login_required
@admin_required
def admin_products(request):
    context = get_admin_context(request)
    products_qs = Product.objects.all().select_related('farmer', 'category').order_by('-created_at')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        products_qs = products_qs.filter(
            Q(name__icontains=search_query) |
            Q(farmer__farm_name__icontains=search_query) |
            Q(category__name__icontains=search_query)
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
            
    paginator = Paginator(products_qs, 10)
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
    return render(request, 'admin_panel/products.html', context)

@login_required
@admin_required
def admin_product_detail(request, id):
    context = get_admin_context(request)
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_availability':
            product.is_available = not product.is_available
            product.save()
            log_admin_action(request, f"Toggled availability status of product {product.name} to {product.is_available}")
            messages.success(request, f"Product availability updated successfully.")
            return redirect('admin_product_detail', id=product.id)
            
        elif action == 'delete_product':
            name = product.name
            product.delete()
            log_admin_action(request, f"Deleted crop listing {name}")
            messages.success(request, f"Product '{name}' deleted successfully.")
            return redirect('admin_products')
            
    context.update({
        'product': product,
    })
    return render(request, 'admin_panel/product_detail.html', context)

@login_required
@admin_required
def admin_categories(request):
    context = get_admin_context(request)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            log_admin_action(request, f"Created category '{category.name}'")
            messages.success(request, f"Category '{category.name}' added successfully!")
            return redirect('admin_categories')
        else:
            messages.error(request, "Failed to create category. Verify forms data.")
    else:
        form = CategoryForm()
        
    categories_qs = Category.objects.all().order_by('-created_at')
    
    # Calculate stats for categories
    categories_list = []
    for cat in categories_qs:
        prod_count = cat.products.count()
        sales_sum = OrderItem.objects.filter(product__category=cat, order__status='DELIVERED').aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
        categories_list.append({
            'category': cat,
            'prod_count': prod_count,
            'sales_sum': sales_sum
        })
        
    context.update({
        'categories_list': categories_list,
        'form': form,
    })
    return render(request, 'admin_panel/categories.html', context)

@login_required
@admin_required
def admin_edit_category(request, id):
    category = get_object_or_404(Category, id=id)
    context = get_admin_context(request)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            log_admin_action(request, f"Updated category '{category.name}'")
            messages.success(request, f"Category '{category.name}' updated successfully!")
            return redirect('admin_categories')
        else:
            messages.error(request, "Failed to update category. Verify forms data.")
    else:
        form = CategoryForm(instance=category)
        
    context.update({
        'category': category,
        'form': form,
    })
    return render(request, 'admin_panel/edit_category.html', context)

@login_required
@admin_required
def admin_orders(request):
    context = get_admin_context(request)
    orders_qs = Order.objects.all().order_by('-created_at')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        orders_qs = orders_qs.filter(
            Q(order_number__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
        
    # Filters
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter.upper())
        
    paginator = Paginator(orders_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context.update({
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_status': status_filter,
    })
    return render(request, 'admin_panel/orders.html', context)

@login_required
@admin_required
def admin_order_detail(request, order_number):
    context = get_admin_context(request)
    order = get_object_or_404(Order, order_number=order_number)
    
    items = order.items.all().select_related('product', 'farmer')
    
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save()
            log_admin_action(request, f"Updated order {order.order_number} status to {order.get_status_display()}")
            messages.success(request, f"Order status updated to {order.get_status_display()} successfully.")
            return redirect('admin_order_detail', order_number=order.order_number)
    else:
        form = OrderStatusForm(instance=order)
        
    context.update({
        'order': order,
        'items': items,
        'form': form,
    })
    return render(request, 'admin_panel/order_detail.html', context)

@login_required
@admin_required
def admin_earnings(request):
    context = get_admin_context(request)
    
    # Platform calculations
    gross_sales = OrderItem.objects.filter(order__status='DELIVERED').aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
    
    # Settings commission calculation
    settings_obj = SiteSettings.objects.first()
    comm_rate = settings_obj.commission_rate if settings_obj else Decimal('10.00')
    
    platform_revenue = gross_sales * (comm_rate / Decimal('100.00'))
    farmer_earnings = gross_sales - platform_revenue
    
    # Available wallet balance for withdrawals
    completed_payouts = Payout.objects.filter(status='COMPLETED').aggregate(sum_amt=Sum('amount'))['sum_amt'] or Decimal('0.00')
    pending_payouts = Payout.objects.filter(status='PENDING').aggregate(sum_amt=Sum('amount'))['sum_amt'] or Decimal('0.00')
    available_balance = farmer_earnings - completed_payouts - pending_payouts
    
    # Top performing farmers
    top_farmers = OrderItem.objects.filter(
        order__status='DELIVERED'
    ).values(
        'farmer__id', 'farmer__farm_name', 'farmer__user__first_name', 'farmer__user__last_name'
    ).annotate(
        sales=Sum('subtotal')
    ).order_by('-sales')[:5]
    
    # Monthly sales curve data (past 6 months)
    today = timezone.localdate()
    months_labels = []
    months_values = []
    for i in range(5, -1, -1):
        target_month = (today.month - i - 1) % 12 + 1
        target_year = today.year if today.month - i > 0 else today.year - 1
        sales_m = OrderItem.objects.filter(
            order__status='DELIVERED',
            order__created_at__month=target_month,
            order__created_at__year=target_year
        ).aggregate(sum_sales=Sum('subtotal'))['sum_sales'] or Decimal('0.00')
        months_labels.append(datetime.date(target_year, target_month, 1).strftime('%B'))
        months_values.append(float(sales_m))
        
    context.update({
        'gross_sales': gross_sales,
        'platform_revenue': platform_revenue,
        'farmer_earnings': farmer_earnings,
        'available_balance': available_balance,
        'pending_payouts': pending_payouts,
        'top_farmers': top_farmers,
        'months_labels': json.dumps(months_labels),
        'months_values': json.dumps(months_values),
    })
    return render(request, 'admin_panel/earnings.html', context)

@login_required
@admin_required
def admin_payouts(request):
    context = get_admin_context(request)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        payout_id = request.POST.get('payout_id')
        payout = get_object_or_404(Payout, id=payout_id)
        
        if action == 'approve' and payout.status == 'PENDING':
            payout.status = 'COMPLETED'
            payout.processed_at = timezone.now()
            payout.save()
            log_admin_action(request, f"Approved payout ID {payout.id} of GHS {payout.amount} for {payout.farmer.farm_name}")
            messages.success(request, f"Payout of GHS {payout.amount:.2f} approved successfully.")
            
            # Notify Farmer
            Notification.objects.create(
                buyer=payout.farmer.user,
                title="Payout Approved!",
                message=f"Your withdrawal request of GHS {payout.amount:.2f} has been processed and completed.",
                notification_type='ORDER_UPDATE'
            )
            return redirect('admin_payouts')
            
        elif action == 'reject' and payout.status == 'PENDING':
            payout.status = 'FAILED'
            payout.save()
            log_admin_action(request, f"Rejected payout ID {payout.id} for {payout.farmer.farm_name}")
            messages.warning(request, f"Payout request rejected.")
            return redirect('admin_payouts')
            
    payouts_qs = Payout.objects.all().select_related('farmer').order_by('-requested_at')
    
    paginator = Paginator(payouts_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context.update({
        'page_obj': page_obj,
    })
    return render(request, 'admin_panel/payouts.html', context)

@login_required
@admin_required
def admin_reviews(request):
    context = get_admin_context(request)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        review_id = request.POST.get('review_id')
        review = get_object_or_404(Review, id=review_id)
        
        if action == 'delete_review':
            review_text = review.comment[:30]
            review.delete()
            log_admin_action(request, f"Deleted review: '{review_text}...'")
            messages.success(request, "Review deleted successfully.")
            return redirect('admin_reviews')
            
    reviews_qs = Review.objects.all().select_related('buyer', 'product').order_by('-created_at')
    
    # Rating aggregates
    avg_rating = reviews_qs.aggregate(avg=Avg('rating'))['avg'] or 4.5
    total_reviews = reviews_qs.count()
    
    rating_breakdown = {}
    for score in range(1, 6):
        count = reviews_qs.filter(rating=score).count()
        percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
        rating_breakdown[score] = {
            'count': count,
            'percentage': round(percentage, 1)
        }
        
    paginator = Paginator(reviews_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context.update({
        'page_obj': page_obj,
        'avg_rating': round(avg_rating, 2),
        'total_reviews': total_reviews,
        'rating_breakdown': rating_breakdown,
    })
    return render(request, 'admin_panel/reviews.html', context)

@login_required
@admin_required
def admin_messages(request):
    context = get_admin_context(request)
    
    conversations = Conversation.objects.all().select_related('buyer', 'farmer').order_by('-updated_at')
    active_conv_id = request.GET.get('conv')
    active_conversation = None
    messages_list = []
    
    if active_conv_id:
        active_conversation = get_object_or_404(Conversation, id=active_conv_id)
        messages_list = active_conversation.messages.all().order_by('created_at')
    elif conversations.exists():
        active_conversation = conversations.first()
        messages_list = active_conversation.messages.all().order_by('created_at')
        
    context.update({
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages_list': messages_list,
    })
    return render(request, 'admin_panel/messages.html', context)

@login_required
@admin_required
def admin_reports(request):
    # Route for PDF/Excel exports overview report
    return redirect('admin_analytics')

@login_required
@admin_required
def admin_analytics(request):
    context = get_admin_context(request)
    
    # Registration analytics metrics
    new_users = User.objects.filter(date_joined__gte=timezone.now() - datetime.timedelta(days=30)).count()
    new_farmers = FarmerProfile.objects.filter(created_at__gte=timezone.now() - datetime.timedelta(days=30)).count()
    new_buyers = User.objects.filter(account_type='BUYER', date_joined__gte=timezone.now() - datetime.timedelta(days=30)).count()
    
    # Conversion Rate estimate placeholders
    conversion_rate = "3.24%"
    
    context.update({
        'new_users': new_users,
        'new_farmers': new_farmers,
        'new_buyers': new_buyers,
        'conversion_rate': conversion_rate,
    })
    return render(request, 'admin_panel/analytics.html', context)

@login_required
@admin_required
def admin_promotions(request):
    context = get_admin_context(request)
    
    if request.method == 'POST':
        form = PromotionForm(request.POST, request.FILES)
        if form.is_valid():
            promotion = form.save()
            log_admin_action(request, f"Created promotional campaign: '{promotion.title}'")
            messages.success(request, f"Campaign '{promotion.title}' added successfully!")
            return redirect('admin_promotions')
    else:
        form = PromotionForm()
        
    promotions = Promotion.objects.all().order_by('-start_date')
    context.update({
        'promotions': promotions,
        'form': form,
    })
    return render(request, 'admin_panel/promotions.html', context)

@login_required
@admin_required
def admin_pages(request):
    context = get_admin_context(request)
    # Simple Content moderation overview template
    return render(request, 'admin_panel/pages.html', context)

@login_required
@admin_required
def admin_settings(request):
    context = get_admin_context(request)
    settings_obj, created = SiteSettings.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            log_admin_action(request, "Updated global site configurations settings.")
            messages.success(request, "Global system configurations saved successfully.")
            return redirect('admin_settings')
        else:
            messages.error(request, "Failed to save settings. Please verify input fields.")
    else:
        form = SettingsForm(instance=settings_obj)
        
    context.update({
        'form': form,
        'settings_obj': settings_obj,
    })
    return render(request, 'admin_panel/settings.html', context)

@login_required
@admin_required
def admin_notifications(request):
    context = get_admin_context(request)
    notifications_list = Notification.objects.filter(buyer=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_all_read':
            Notification.objects.filter(buyer=request.user, is_read=False).update(is_read=True)
            messages.success(request, "All admin alerts marked as read.")
            return redirect('admin_notifications')
            
    context.update({
        'notifications': notifications_list,
    })
    return render(request, 'admin_panel/notifications.html', context)

@login_required
@admin_required
def admin_logs(request):
    context = get_admin_context(request)
    logs_qs = ActivityLog.objects.all().select_related('admin').order_by('-created_at')
    
    paginator = Paginator(logs_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context.update({
        'page_obj': page_obj,
    })
    return render(request, 'admin_panel/activity_logs.html', context)

@login_required
@admin_required
def admin_support(request):
    context = get_admin_context(request)
    tickets_qs = SupportTicket.objects.all().select_related('user').order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status', '')
    if status_filter:
        tickets_qs = tickets_qs.filter(status=status_filter.upper())
        
    paginator = Paginator(tickets_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context.update({
        'page_obj': page_obj,
        'selected_status': status_filter,
    })
    return render(request, 'admin_panel/support.html', context)

@login_required
@admin_required
def admin_ticket_detail(request, id):
    context = get_admin_context(request)
    ticket = get_object_or_404(SupportTicket, id=id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'reply_message':
            form = SupportTicketReplyForm(request.POST)
            if form.is_valid():
                reply = form.save(commit=False)
                reply.ticket = ticket
                reply.sender = request.user
                reply.save()
                
                # Automatically advance status to In Progress
                if ticket.status == 'OPEN':
                    ticket.status = 'IN_PROGRESS'
                    ticket.save()
                    
                log_admin_action(request, f"Submitted official reply on support ticket ID {ticket.id}")
                messages.success(request, "Your reply has been submitted successfully.")
                return redirect('admin_ticket_detail', id=ticket.id)
                
        elif action == 'resolve_ticket':
            ticket.status = 'RESOLVED'
            ticket.save()
            log_admin_action(request, f"Marked support ticket ID {ticket.id} as RESOLVED")
            messages.success(request, "Ticket marked as resolved successfully.")
            return redirect('admin_ticket_detail', id=ticket.id)
            
        elif action == 'close_ticket':
            ticket.status = 'CLOSED'
            ticket.save()
            log_admin_action(request, f"Marked support ticket ID {ticket.id} as CLOSED")
            messages.warning(request, "Ticket has been closed.")
            return redirect('admin_ticket_detail', id=ticket.id)
            
    form = SupportTicketReplyForm()
    messages_list = ticket.messages.all().select_related('sender').order_by('created_at')
    
    context.update({
        'ticket': ticket,
        'form': form,
        'messages_list': messages_list,
    })
    return render(request, 'admin_panel/ticket_detail.html', context)

@login_required
@admin_required
def admin_profile(request):
    context = get_admin_context(request)
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            form = AdminProfileForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                log_admin_action(request, "Updated admin personal profile attributes details.")
                messages.success(request, "Profile updated successfully.")
                return redirect('admin_profile')
            else:
                messages.error(request, "Failed to update profile details.")
                
        elif action == 'change_password':
            form_pwd = PasswordChangeForm(user, request.POST)
            if form_pwd.is_valid():
                user_updated = form_pwd.save()
                update_session_auth_hash(request, user_updated)
                log_admin_action(request, "Updated admin access password credentials.")
                messages.success(request, "Password changed successfully.")
                return redirect('admin_profile')
            else:
                messages.error(request, "Password change failed. Check inputs.")
                
    form = AdminProfileForm(instance=user)
    form_pwd = PasswordChangeForm(user)
    
    context.update({
        'form': form,
        'form_pwd': form_pwd,
    })
    return render(request, 'admin_panel/profile.html', context)
