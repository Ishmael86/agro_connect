from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from farmers.models import FarmerProfile
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Sum, Q
from decimal import Decimal
import uuid

# Models
from django.contrib.auth import get_user_model
from accounts.models import BuyerProfile, Wishlist, Address, Conversation, Message
from payments.models import PaymentMethod
from products.models import Product, Category, Review
from notifications.models import Notification
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from farmers.models import FarmerProfile

# Forms
from accounts.forms import AddressForm, PaymentMethodForm, ReviewForm, ProfileForm

User = get_user_model()

def buyer_required(view_func):
    """Decorator to ensure only BUYER accounts can access the view."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.account_type != 'BUYER':
            messages.error(request, "Access restricted to Buyer accounts.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

def get_buyer_context(request):
    """Utility helper to get common badge counts and profiles."""
    user = request.user
    # Ensure profile exists
    profile, _ = BuyerProfile.objects.get_or_create(user=user)
    
    # Get guest or authenticated cart
    cart = None
    cart_count = 0
    if user.is_authenticated:
        cart = Cart.objects.filter(user=user).first()
    else:
        session_key = request.session.session_key
        if session_key:
            cart = Cart.objects.filter(session_key=session_key).first()
    if cart:
        cart_count = cart.total_items
        
    unread_messages = Message.objects.filter(conversation__buyer=user, is_read=False).exclude(sender=user).count()
    unread_notifications = Notification.objects.filter(buyer=user, is_read=False).count()
    
    return {
        'buyer_profile': profile,
        'cart_count': cart_count,
        'unread_messages': unread_messages,
        'unread_notifications': unread_notifications,
    }

@login_required
@buyer_required
def buyer_dashboard(request):
    user = request.user
    context = get_buyer_context(request)
    
    # Calculations
    orders = Order.objects.filter(user=user).order_by('-created_at')
    total_orders = orders.count()
    pending_orders = orders.filter(status='PENDING').count()
    completed_orders = orders.filter(status='DELIVERED').count()
    total_spent = orders.filter(status='DELIVERED').aggregate(sum_total=Sum('total'))['sum_total'] or Decimal('0.00')
    wishlist_count = Wishlist.objects.filter(buyer=user).count()
    reward_points = context['buyer_profile'].reward_points
    
    # Recent orders
    recent_orders = orders[:5]
    
    # Recommendations (popular or featured crops)
    recommended = Product.objects.filter(is_available=True).order_by('-rating')[:3]
    
    context.update({
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_spent': total_spent,
        'wishlist_count': wishlist_count,
        'reward_points': reward_points,
        'recent_orders': recent_orders,
        'recommended': recommended,
    })
    return render(request, 'buyer/dashboard.html', context)

@login_required
@buyer_required
def buyer_orders(request):
    user = request.user
    context = get_buyer_context(request)
    
    status_filter = request.GET.get('status', 'all').upper()
    orders_query = Order.objects.filter(user=user).order_by('-created_at')
    
    if status_filter != 'ALL':
        orders_query = orders_query.filter(status=status_filter)
        
    paginator = Paginator(orders_query, 5) # 5 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context.update({
        'orders': page_obj,
        'status_filter': status_filter.lower(),
    })
    return render(request, 'buyer/orders.html', context)

@login_required
@buyer_required
def buyer_order_detail(request, order_number):
    user = request.user
    context = get_buyer_context(request)
    
    # Retrieve order and ensure ownership
    order = get_object_or_404(Order.objects.prefetch_related('items__product__farmer'), order_number=order_number, user=user)
    
    context.update({
        'order': order,
        'items': order.items.all(),
    })
    return render(request, 'buyer/order_detail.html', context)

@login_required
@buyer_required
def buyer_cart(request):
    user = request.user
    context = get_buyer_context(request)
    
    cart, created = Cart.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        item_id = request.POST.get('item_id')
        
        if action == 'update_quantity' and item_id:
            direction = request.POST.get('direction')
            item = get_object_or_404(CartItem, id=item_id, cart=cart)
            if direction == 'up':
                if item.quantity < item.product.stock_quantity:
                    item.quantity += 1
                    item.save()
                else:
                    messages.warning(request, f"Sorry, only {item.product.stock_quantity} units available in stock.")
            elif direction == 'down':
                if item.quantity > 1:
                    item.quantity -= 1
                    item.save()
                else:
                    item.delete()
                    messages.success(request, "Item removed from cart.")
                    
        elif action == 'remove_item' and item_id:
            item = get_object_or_404(CartItem, id=item_id, cart=cart)
            item.delete()
            messages.success(request, "Item removed from cart.")
            
        elif action == 'buy_again':
            order_id = request.POST.get('order_id')
            if order_id:
                order = get_object_or_404(Order, id=order_id, user=user)
                for order_item in order.items.all():
                    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=order_item.product)
                    if created:
                        cart_item.quantity = order_item.quantity
                    else:
                        cart_item.quantity += order_item.quantity
                    # Ensure stock limit
                    if cart_item.quantity > order_item.product.stock_quantity:
                        cart_item.quantity = order_item.product.stock_quantity
                    cart_item.save()
                messages.success(request, "Items added back to your cart.")
                return redirect('buyer_cart')
                
        return redirect('buyer_cart')
        
    items = cart.items.all().select_related('product')
    subtotal = cart.total_price
    delivery_fee = Decimal('0.00') if subtotal >= Decimal('300.00') or subtotal == 0 else Decimal('10.00')
    total = subtotal + delivery_fee
    
    away_from_free = Decimal('300.00') - subtotal
    if away_from_free < 0:
        away_from_free = Decimal('0.00')
        
    context.update({
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'away_from_free': away_from_free,
        'progress_pct': min(int((subtotal / Decimal('300.00')) * 100), 100),
    })
    return render(request, 'buyer/cart.html', context)

@login_required
@buyer_required
def buyer_checkout(request):
    user = request.user
    context = get_buyer_context(request)
    
    cart = Cart.objects.filter(user=user).first()
    if not cart or cart.total_items == 0:
        messages.error(request, "Your cart is empty. Please add items before checking out.")
        return redirect('buyer_cart')
        
    items = cart.items.all().select_related('product')
    
    subtotal = cart.total_price
    delivery_fee = Decimal('0.00') if subtotal >= Decimal('300.00') else Decimal('10.00')
    total = subtotal + delivery_fee
    
    # Fetch saved addresses and payment options
    addresses = Address.objects.filter(buyer=user)
    payment_methods = PaymentMethod.objects.filter(buyer=user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        selected_address_id = request.POST.get('selected_address')
        selected_payment_id = request.POST.get('selected_payment')
        
        address_obj = None
        if selected_address_id:
            address_obj = Address.objects.filter(id=selected_address_id, buyer=user).first()
            
        payment_obj = None
        if selected_payment_id:
            payment_obj = PaymentMethod.objects.filter(id=selected_payment_id, buyer=user).first()
            
        # If no saved address, validate the address input form
        if not address_obj:
            if form.is_valid():
                address_obj = form.save(commit=False)
                address_obj.buyer = user
                address_obj.save()
            else:
                messages.error(request, "Please select an address or complete the form details.")
                context.update({
                    'form': form,
                    'addresses': addresses,
                    'payment_methods': payment_methods,
                    'items': items,
                    'subtotal': subtotal,
                    'delivery_fee': delivery_fee,
                    'total': total,
                })
                return render(request, 'buyer/checkout.html', context)
                
        payment_method_val = 'MOBILE_MONEY'
        if payment_obj:
            payment_method_val = 'CARD_PAYMENT' if payment_obj.payment_type == 'CARD' else 'MOBILE_MONEY'
        else:
            payment_method_val = request.POST.get('payment_method_raw', 'MOBILE_MONEY')
            
        try:
            with transaction.atomic():
                unique_id = uuid.uuid4().hex[:6].upper()
                order_number = f"AGC-2026-{unique_id}"
                
                order = Order.objects.create(
                    user=user,
                    order_number=order_number,
                    full_name=address_obj.full_name,
                    phone=address_obj.phone,
                    delivery_address=address_obj.address,
                    region=address_obj.region,
                    city=address_obj.city,
                    payment_method=payment_method_val,
                    subtotal=subtotal,
                    delivery_fee=delivery_fee,
                    total=total,
                    status='PENDING'
                )
                
                # Copy cart items to order items and reduce stock
                for item in items:
                    product = item.product
                    if product.stock_quantity < item.quantity:
                        raise ValueError(f"Insufficient stock for {product.name}.")
                        
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        farmer=product.farmer,
                        quantity=item.quantity,
                        unit_price=product.final_price,
                        subtotal=item.subtotal
                    )
                    
                    product.stock_quantity -= item.quantity
                    product.save()
                    
                # Increment reward points
                profile = context['buyer_profile']
                profile.reward_points += int(subtotal / Decimal('10.00')) # 1 point per 10 GHS
                profile.save()
                
                # Clear cart
                cart.items.all().delete()
                
                # Generate Success Notification
                Notification.objects.create(
                    buyer=user,
                    title="Order Placed Successfully",
                    message=f"Your order {order_number} has been created and is awaiting farmer confirmation.",
                    notification_type="ORDER_UPDATE"
                )
                
                messages.success(request, "Order placed successfully!")
                return redirect('order_success', order_number=order_number)
                
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            
    else:
        # Prepopulate form with default address if exists
        default_address = Address.objects.filter(buyer=user, is_default=True).first()
        initial_data = {}
        if default_address:
            initial_data = {
                'full_name': default_address.full_name,
                'phone': default_address.phone,
                'region': default_address.region,
                'city': default_address.city,
                'address': default_address.address,
                'additional_information': default_address.additional_information,
            }
        form = AddressForm(initial=initial_data)
        
    context.update({
        'form': form,
        'addresses': addresses,
        'payment_methods': payment_methods,
        'items': items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
    })
    return render(request, 'buyer/checkout.html', context)

@login_required
@buyer_required
def buyer_wishlist(request):
    user = request.user
    context = get_buyer_context(request)
    
    # Handle AJAX wishlist action
    if request.method == 'POST':
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        
        if action == 'toggle' and product_id:
            product = get_object_or_404(Product, id=product_id)
            wish, created = Wishlist.objects.get_or_create(buyer=user, product=product)
            if not created:
                wish.delete()
                return JsonResponse({'status': 'removed', 'message': f'{product.name} removed from wishlist.'})
            return JsonResponse({'status': 'added', 'message': f'{product.name} added to wishlist.'})
            
        elif action == 'move_all_to_cart':
            wishlist_items = Wishlist.objects.filter(buyer=user)
            cart, _ = Cart.objects.get_or_create(user=user)
            added_count = 0
            
            for item in wishlist_items:
                # Add to cart
                cart_item, created = CartItem.objects.get_or_create(cart=cart, product=item.product)
                if not created:
                    cart_item.quantity += 1
                cart_item.save()
                added_count += 1
                
            wishlist_items.delete()
            messages.success(request, f"Moved {added_count} items from wishlist to cart.")
            return redirect('buyer_cart')
            
    items = Wishlist.objects.filter(buyer=user).select_related('product__farmer')
    context.update({
        'items': items,
    })
    return render(request, 'buyer/wishlist.html', context)

@login_required
@buyer_required
def buyer_addresses(request):
    user = request.user
    context = get_buyer_context(request)
    
    addresses = Address.objects.filter(buyer=user).order_by('-is_default', '-created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        address_id = request.POST.get('address_id')
        
        if action == 'add':
            form = AddressForm(request.POST)
            if form.is_valid():
                address_obj = form.save(commit=False)
                address_obj.buyer = user
                if address_obj.is_default:
                    Address.objects.filter(buyer=user).update(is_default=False)
                address_obj.save()
                messages.success(request, "New address added successfully.")
            else:
                messages.error(request, "Failed to add address. Check input fields.")
                
        elif action == 'delete' and address_id:
            addr = get_object_or_404(Address, id=address_id, buyer=user)
            addr.delete()
            messages.success(request, "Address deleted successfully.")
            
        elif action == 'set_default' and address_id:
            Address.objects.filter(buyer=user).update(is_default=False)
            addr = get_object_or_404(Address, id=address_id, buyer=user)
            addr.is_default = True
            addr.save()
            messages.success(request, "Default address updated.")
            
        return redirect('buyer_addresses')
        
    form = AddressForm()
    context.update({
        'addresses': addresses,
        'form': form,
    })
    return render(request, 'buyer/addresses.html', context)

@login_required
@buyer_required
def buyer_payments(request):
    user = request.user
    context = get_buyer_context(request)
    
    payments = PaymentMethod.objects.filter(buyer=user).order_by('-is_default')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        payment_id = request.POST.get('payment_id')
        
        if action == 'add':
            form = PaymentMethodForm(request.POST)
            if form.is_valid():
                pm = form.save(commit=False)
                pm.buyer = user
                if pm.is_default:
                    PaymentMethod.objects.filter(buyer=user).update(is_default=False)
                pm.save()
                messages.success(request, "Payment method saved successfully.")
            else:
                messages.error(request, "Failed to save payment method.")
                
        elif action == 'delete' and payment_id:
            pm = get_object_or_404(PaymentMethod, id=payment_id, buyer=user)
            pm.delete()
            messages.success(request, "Payment method removed.")
            
        elif action == 'set_default' and payment_id:
            PaymentMethod.objects.filter(buyer=user).update(is_default=False)
            pm = get_object_or_404(PaymentMethod, id=payment_id, buyer=user)
            pm.is_default = True
            pm.save()
            messages.success(request, "Default payment method updated.")
            
        return redirect('buyer_payments')
        
    form = PaymentMethodForm()
    context.update({
        'payments': payments,
        'form': form,
    })
    return render(request, 'buyer/payments.html', context)

@login_required
@buyer_required
def buyer_reviews(request):
    user = request.user
    context = get_buyer_context(request)
    
    # Get products purchased by the buyer that they have not reviewed yet
    orders = Order.objects.filter(user=user, status='DELIVERED')
    purchased_product_ids = OrderItem.objects.filter(order__in=orders).values_list('product_id', flat=True).distinct()
    
    reviewed_product_ids = Review.objects.filter(buyer=user).values_list('product_id', flat=True)
    unreviewed_products = Product.objects.filter(id__in=purchased_product_ids).exclude(id__in=reviewed_product_ids)
    
    my_reviews = Review.objects.filter(buyer=user).select_related('product')
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        form = ReviewForm(request.POST)
        
        if form.is_valid() and product_id:
            prod = get_object_or_404(Product, id=product_id)
            review = form.save(commit=False)
            review.buyer = user
            review.product = prod
            review.save()
            
            # Recalculate product rating
            all_reviews = Review.objects.filter(product=prod)
            avg_rating = sum(r.rating for r in all_reviews) / all_reviews.count()
            prod.rating = Decimal(str(round(avg_rating, 2)))
            prod.review_count = all_reviews.count()
            prod.save()
            
            messages.success(request, "Thank you! Your review has been posted.")
            return redirect('buyer_reviews')
            
    form = ReviewForm()
    context.update({
        'unreviewed_products': unreviewed_products,
        'my_reviews': my_reviews,
        'form': form,
    })
    return render(request, 'buyer/reviews.html', context)

@login_required
@buyer_required
def buyer_messages(request):
    user = request.user
    context = get_buyer_context(request)
    
    # Fetch user conversations
    conversations = Conversation.objects.filter(buyer=user).select_related('farmer').order_by('-updated_at')
    
    active_conv_id = request.GET.get('conv')
    active_conversation = None
    messages_list = []
    
    if active_conv_id:
        active_conversation = get_object_or_404(Conversation, id=active_conv_id, buyer=user)
        # Mark incoming messages as read
        Message.objects.filter(conversation=active_conversation, is_read=False).exclude(sender=user).update(is_read=True)
        messages_list = active_conversation.messages.all().order_by('created_at')
        
    elif conversations.exists():
        # Load the latest conversation as default
        active_conversation = conversations.first()
        Message.objects.filter(conversation=active_conversation, is_read=False).exclude(sender=user).update(is_read=True)
        messages_list = active_conversation.messages.all().order_by('created_at')
        
    if request.method == 'POST' and active_conversation:
        msg_text = request.POST.get('message_text')
        if msg_text:
            Message.objects.create(
                conversation=active_conversation,
                sender=user,
                message=msg_text
            )
            # Update timestamp
            active_conversation.save()
            return redirect(reverse('buyer_messages') + f"?conv={active_conversation.id}")
            
    context.update({
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages_list': messages_list,
    })
    return render(request, 'buyer/messages.html', context)

@login_required
@buyer_required
def buyer_messages_init(request, farmer_id):
    farmer = get_object_or_404(FarmerProfile, id=farmer_id)
    # Check if a conversation already exists
    conv, created = Conversation.objects.get_or_create(buyer=request.user, farmer=farmer)
    return redirect(reverse('buyer_messages') + f"?conv={conv.id}")

@login_required
@buyer_required
def buyer_notifications(request):
    user = request.user
    context = get_buyer_context(request)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notification_id = request.POST.get('notification_id')
        
        if action == 'mark_read' and notification_id:
            notif = get_object_or_404(Notification, id=notification_id, buyer=user)
            notif.is_read = True
            notif.save()
            return JsonResponse({'status': 'success'})
            
        elif action == 'mark_all_read':
            Notification.objects.filter(buyer=user, is_read=False).update(is_read=True)
            messages.success(request, "All notifications marked as read.")
            return redirect('buyer_notifications')
            
    notifications = Notification.objects.filter(buyer=user).order_by('-created_at')
    context.update({
        'notifications': notifications,
    })
    return render(request, 'buyer/notifications.html', context)

@login_required
@buyer_required
def buyer_settings(request):
    user = request.user
    context = get_buyer_context(request)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_account':
            user.delete()
            messages.success(request, "Your account has been deleted successfully.")
            return redirect('home')
            
        messages.success(request, "Settings updated successfully.")
        return redirect('buyer_settings')
        
    return render(request, 'buyer/settings.html', context)

@login_required
@buyer_required
def buyer_profile(request):
    user = request.user
    context = get_buyer_context(request)
    
    profile = context['buyer_profile']
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            
            # Save phone & image into BuyerProfile
            profile.phone = form.cleaned_data['phone']
            if 'profile_image' in request.FILES:
                profile.profile_image = request.FILES['profile_image']
            profile.save()
            
            messages.success(request, "Profile updated successfully.")
            return redirect('buyer_profile')
        else:
            messages.error(request, "Error updating profile details.")
    else:
        form = ProfileForm(instance=user, initial={'phone': profile.phone})
        
    context.update({
        'form': form,
    })
    return render(request, 'buyer/profile.html', context)

@login_required
@buyer_required
def buyer_change_password(request):
    user = request.user
    context = get_buyer_context(request)
    
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) # Prevents logging out
            messages.success(request, "Password updated successfully.")
            return redirect('buyer_settings')
        else:
            messages.error(request, "Failed to update password. Check input fields.")
    else:
        form = PasswordChangeForm(user)
        
    context.update({
        'form': form,
    })
    return render(request, 'buyer/change_password.html', context)

@login_required
@buyer_required
def buyer_help(request):
    context = get_buyer_context(request)
    return render(request, 'buyer/help.html', context)

@login_required
@buyer_required
def buyer_download_invoice(request, order_number):
    from io import BytesIO
    from django.template.loader import get_template
    from django.http import HttpResponse
    from xhtml2pdf import pisa

    user = request.user
    order = get_object_or_404(Order, order_number=order_number, user=user)
    items = order.items.all().select_related('product', 'product__category')
    
    context = {
        'order': order,
        'items': items,
    }
    
    template = get_template('buyer/invoice_pdf.html')
    html = template.render(context)
    
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f"Invoice-{order.order_number}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    return HttpResponse("Error generating invoice PDF", status=500)


@login_required
def ajax_get_messages(request, conv_id):
    """AJAX endpoint to get all messages for a specific conversation."""
    conv = get_object_or_404(Conversation, id=conv_id)
    # Security check: User must be either the buyer or the farmer user
    if request.user != conv.buyer and request.user != conv.farmer.user:
        return JsonResponse({'success': False, 'message': 'Access denied.'}, status=403)
        
    last_msg_id = request.GET.get('last_msg_id')
    messages_qs = conv.messages.all().order_by('created_at')
    
    if last_msg_id:
        messages_qs = messages_qs.filter(id__gt=last_msg_id)
        
    messages_data = []
    for msg in messages_qs:
        # Mark as read if the current user is not the sender
        if msg.sender != request.user and not msg.is_read:
            msg.is_read = True
            msg.save()
            
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_username': msg.sender.username,
            'message': msg.message,
            'is_outgoing': msg.sender == request.user,
            'created_at': msg.created_at.strftime('%I:%M %p'),
        })
        
    return JsonResponse({
        'success': True,
        'messages': messages_data
    })


@login_required
def ajax_send_message(request, conv_id):
    """AJAX endpoint to send a message to a specific conversation."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)
        
    conv = get_object_or_404(Conversation, id=conv_id)
    # Security check: User must be either the buyer or the farmer user
    if request.user != conv.buyer and request.user != conv.farmer.user:
        return JsonResponse({'success': False, 'message': 'Access denied.'}, status=403)
        
    msg_text = request.POST.get('message_text')
    if not msg_text or not msg_text.strip():
        return JsonResponse({'success': False, 'message': 'Message cannot be empty.'}, status=400)
        
    msg = Message.objects.create(
        conversation=conv,
        sender=request.user,
        message=msg_text.strip()
    )
    # Update timestamp
    conv.save()
    
    return JsonResponse({
        'success': True,
        'message_data': {
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_username': msg.sender.username,
            'message': msg.message,
            'is_outgoing': True,
            'created_at': msg.created_at.strftime('%I:%M %p'),
        }
    })
