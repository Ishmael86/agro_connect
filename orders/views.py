import uuid
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from cart.models import Cart
from .models import Order, OrderItem
from .forms import CheckoutForm

def checkout_view(request):
    # Fetch cart
    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        if session_key:
            cart = Cart.objects.filter(session_key=session_key).first()
            
    if not cart or cart.total_items == 0:
        messages.error(request, "Your cart is empty. Please add some products before checking out.")
        return redirect('product_list')
        
    items = cart.items.all().select_related('product')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Generate a unique order number
                    # Pattern: AGC-2026-XXXXX
                    unique_id = uuid.uuid4().hex[:6].upper()
                    order_number = f"AGC-2026-{unique_id}"
                    
                    order = form.save(commit=False)
                    order.order_number = order_number
                    order.subtotal = cart.total_price
                    order.delivery_fee = Decimal('10.00') # GHS 10 flat rate
                    order.total = order.subtotal + order.delivery_fee
                    
                    if request.user.is_authenticated:
                        order.user = request.user
                        
                    order.save()
                    
                    # Create OrderItems and reduce stock
                    for item in items:
                        product = item.product
                        if product.stock_quantity < item.quantity:
                            # Not enough stock, raise exception to rollback transaction
                            raise ValueError(f"Sorry, {product.name} only has {product.stock_quantity} units left in stock.")
                            
                        # Create OrderItem
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            farmer=product.farmer,
                            quantity=item.quantity,
                            unit_price=product.final_price,
                            subtotal=item.subtotal
                        )
                        
                        # Reduce stock
                        product.stock_quantity -= item.quantity
                        if product.stock_quantity == 0:
                            product.is_available = False
                        product.save()
                        
                    # Clear Cart
                    cart.items.all().delete()
                    
                    messages.success(request, "Your order has been placed successfully!")
                    return redirect('order_success', order_number=order_number)
                    
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"An error occurred while processing your order: {str(e)}")
        else:
            messages.error(request, "Please check the form inputs and try again.")
    else:
        # Prepopulate name, phone if user is authenticated
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'full_name': request.user.get_full_name() or request.user.username,
                'phone': request.user.phone or '',
            }
        form = CheckoutForm(initial=initial_data)
        
    context = {
        'form': form,
        'cart': cart,
        'items': items,
        'subtotal': cart.total_price,
        'delivery_fee': Decimal('10.00'),
        'total': cart.total_price + Decimal('10.00'),
    }
    return render(request, 'orders/checkout.html', context)

def order_success_view(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), order_number=order_number)
    
    # Simple security verification: ensure only the owner can view (if authenticated)
    if order.user and order.user != request.user:
        messages.error(request, "You do not have permission to view this order details.")
        return redirect('home')
        
    context = {
        'order': order,
        'items': order.items.all(),
    }
    return render(request, 'orders/success.html', context)
