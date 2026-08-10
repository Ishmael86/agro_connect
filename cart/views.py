from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from products.models import Product
from .models import Cart, CartItem

def get_or_create_cart(request):
    """Helper function to fetch or initialize cart for user or guest."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart

def cart_view(request):
    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        if session_key:
            cart = Cart.objects.filter(session_key=session_key).first()
            
    items = cart.items.all().select_related('product') if cart else []
    
    context = {
        'cart': cart,
        'items': items,
    }
    return render(request, 'cart/cart.html', context)

@require_POST
def cart_add_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if not product.is_available or product.stock_quantity <= 0:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Product is currently out of stock.'}, status=400)
        messages.error(request, f"{product.name} is currently out of stock.")
        return redirect(request.META.get('HTTP_REFERER', 'product_list'))

    cart = get_or_create_cart(request)
    
    with transaction.atomic():
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            new_qty = cart_item.quantity + quantity
        else:
            new_qty = quantity
            
        if new_qty > product.stock_quantity:
            new_qty = product.stock_quantity
            message = f"Only {product.stock_quantity} units available. Cart updated to maximum stock."
            success_status = True
        else:
            message = f"Added {quantity} x {product.name} to your cart."
            success_status = True

        cart_item.quantity = new_qty
        cart_item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': success_status, 
            'message': message,
            'cart_count': cart.total_items
        })
        
    messages.success(request, message)
    return redirect('cart')

@require_POST
def cart_update_view(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = cart_item.cart
    
    # Security check: Ensure cart matches user/session
    if request.user.is_authenticated:
        if cart.user != request.user:
            return JsonResponse({'success': False, 'message': 'Access Denied'}, status=403)
    else:
        if cart.session_key != request.session.session_key:
            return JsonResponse({'success': False, 'message': 'Access Denied'}, status=403)

    action = request.POST.get('action')
    product = cart_item.product
    
    if action == 'increase':
        if cart_item.quantity < product.stock_quantity:
            cart_item.quantity += 1
            cart_item.save()
            msg = "Quantity updated."
            success = True
        else:
            msg = f"Cannot add more. Only {product.stock_quantity} units in stock."
            success = False
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            msg = "Quantity updated."
            success = True
        else:
            cart_item.delete()
            msg = f"Removed {product.name} from cart."
            success = True
            cart_item = None
    else:
        try:
            qty = int(request.POST.get('quantity'))
            if qty <= 0:
                cart_item.delete()
                msg = f"Removed {product.name} from cart."
                success = True
                cart_item = None
            elif qty <= product.stock_quantity:
                cart_item.quantity = qty
                cart_item.save()
                msg = "Quantity updated."
                success = True
            else:
                cart_item.quantity = product.stock_quantity
                cart_item.save()
                msg = f"Only {product.stock_quantity} units available. Set to max stock."
                success = True
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid quantity'}, status=400)

    # Return updated values for local DOM manipulation
    return JsonResponse({
        'success': success,
        'message': msg,
        'item_quantity': cart_item.quantity if cart_item else 0,
        'item_subtotal': f"GHS {cart_item.subtotal:.2f}" if cart_item else "GHS 0.00",
        'cart_subtotal': f"GHS {cart.total_price:.2f}",
        'cart_total': f"GHS {cart.total_price + 10:.2f}", # GHS 10 flat delivery fee
        'cart_count': cart.total_items
    })

@require_POST
def cart_remove_view(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = cart_item.cart
    
    # Security check
    if request.user.is_authenticated:
        if cart.user != request.user:
            messages.error(request, "Access Denied.")
            return redirect('cart')
    else:
        if cart.session_key != request.session.session_key:
            messages.error(request, "Access Denied.")
            return redirect('cart')
            
    product_name = cart_item.product.name
    cart_item.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Removed {product_name} from your cart.",
            'cart_subtotal': f"GHS {cart.total_price:.2f}",
            'cart_total': f"GHS {cart.total_price + 10:.2f}",
            'cart_count': cart.total_items
        })
        
    messages.success(request, f"Removed {product_name} from your cart.")
    return redirect('cart')
