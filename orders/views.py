import uuid
import requests
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.conf import settings
from django.urls import reverse
from cart.models import Cart
from .models import Order, OrderItem
from .forms import CheckoutForm

def send_order_confirmation_email(order, user_email):
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string, get_template
    from io import BytesIO
    from xhtml2pdf import pisa
    
    subject = f"AgroConnect Order Invoice - {order.order_number}"
    recipient_email = user_email if user_email else "buyer@example.com"
    
    # 1. Generate HTML email body
    items = order.items.all().select_related('product', 'farmer')
    html_body = render_to_string('orders/email_invoice.html', {
        'order': order,
        'items': items
    })
    
    email = EmailMessage(
        subject=subject,
        body=html_body,
        from_email='noreply@agroconnect.com',
        to=[recipient_email]
    )
    email.content_subtype = "html" # Send as HTML
    
    # 2. Render PDF invoice & attach
    try:
        pdf_template = get_template('buyer/invoice_pdf.html')
        pdf_html = pdf_template.render({
            'order': order,
            'items': items
        })
        pdf_result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(pdf_html.encode("UTF-8")), pdf_result)
        
        if not pdf.err:
            email.attach(f"Invoice-{order.order_number}.pdf", pdf_result.getvalue(), "application/pdf")
    except Exception:
        pass
        
    try:
        email.send(fail_silently=True)
    except Exception:
        pass

def checkout_view(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in or create an account to place your order.")
        return redirect('login')
        
    if request.user.account_type == 'FARMER':
        messages.warning(request, "Farmers are not allowed to checkout or buy crops. Redirected to your dashboard.")
        return redirect('farmer_dashboard')
        
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
                # 1. Pre-validation: verify all products in items have enough stock before starting payment!
                for item in items:
                    if item.product.stock_quantity < item.quantity:
                        raise ValueError(f"Sorry, {item.product.name} only has {item.product.stock_quantity} units left in stock.")
                
                with transaction.atomic():
                    # Generate a unique order number
                    # Pattern: AGC-2026-XXXXX
                    unique_id = uuid.uuid4().hex[:6].upper()
                    order_number = f"AGC-2026-{unique_id}"
                    
                    order = form.save(commit=False)
                    order.order_number = order_number
                    order.subtotal = cart.total_price
                    order.delivery_fee = Decimal('0.00') # GHS 0 flat rate
                    order.total = order.subtotal + order.delivery_fee
                    
                    if request.user.is_authenticated:
                        order.user = request.user
                    
                    order.payment_status = Order.PaymentStatusChoices.UNPAID
                    order.save()
                    
                    # Create OrderItems (Stock is reduced only after payment succeeds, but we create items first)
                    for item in items:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            farmer=item.product.farmer,
                            quantity=item.quantity,
                            unit_price=item.product.final_price,
                            subtotal=item.subtotal
                        )
                
                # 2. Redirect to Paystack if MOBILE_MONEY or CARD_PAYMENT is selected
                if order.payment_method in (Order.PaymentMethodChoices.MOBILE_MONEY, Order.PaymentMethodChoices.CARD_PAYMENT):
                    paystack_url = "https://api.paystack.co/transaction/initialize"
                    callback_url = request.build_absolute_uri(reverse('paystack_callback'))
                    
                    # Paystack expects amount in sub-units (e.g. kobo or pesewas), which is amount * 100
                    amount_in_pesewas = int(order.total * 100)
                    
                    headers = {
                        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "email": request.user.email if request.user.email else "buyer@example.com",
                        "amount": amount_in_pesewas,
                        "reference": order.order_number,
                        "callback_url": callback_url
                    }
                    
                    response = requests.post(paystack_url, json=payload, headers=headers)
                    response_data = response.json()
                    
                    if response.status_code == 200 and response_data.get('status'):
                        authorization_url = response_data['data']['authorization_url']
                        return redirect(authorization_url)
                    else:
                        error_msg = response_data.get('message', 'Failed to initialize payment gateway.')
                        # Clean up order if payment fails to initialize
                        order.delete()
                        messages.error(request, f"Payment Gateway Error: {error_msg}")
                        return redirect('checkout')
                
                # 3. Cash on Delivery (simulates successful checkout instantly)
                else:
                    with transaction.atomic():
                        # Reduce stock since CoD is confirmed immediately
                        for item in order.items.all():
                            product = item.product
                            if product.stock_quantity < item.quantity:
                                raise ValueError(f"Sorry, {product.name} only has {product.stock_quantity} units left in stock.")
                            product.stock_quantity -= item.quantity
                            if product.stock_quantity == 0:
                                product.is_available = False
                            product.save()
                        
                        # Clear Cart
                        cart.items.all().delete()
                    
                    # Send Order Confirmation Email for CoD
                    send_order_confirmation_email(order, request.user.email if request.user.is_authenticated else "buyer@example.com")
                    
                    messages.success(request, "Your order has been placed successfully!")
                    return redirect('order_success', order_number=order.order_number)
                    
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"An error occurred while processing your order: {str(e)}")
        else:
            messages.error(request, "Please check the form inputs and try again.")
    else:
        # Prepopulate name, phone if user is authenticated
        initial_data = {}
        if request.user.is_authenticated and not (request.user.is_superuser or request.user.is_staff):
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
        'delivery_fee': Decimal('0.00'),
        'total': cart.total_price + Decimal('0.00'),
    }
    return render(request, 'orders/checkout.html', context)

def paystack_callback_view(request):
    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, "No transaction reference provided by payment portal.")
        return redirect('checkout')
        
    order = get_object_or_404(Order, order_number=reference)
    
    # Check if order is already processed
    if order.payment_status == Order.PaymentStatusChoices.PAID:
        return redirect('order_success', order_number=order.order_number)
        
    # Verify transaction with Paystack API
    verify_url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }
    
    try:
        response = requests.get(verify_url, headers=headers)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('status') and response_data['data']['status'] == 'success':
            data = response_data['data']
            
            with transaction.atomic():
                # Verify stock one final time and deduct
                for item in order.items.all():
                    product = item.product
                    if product.stock_quantity < item.quantity:
                        raise ValueError(f"Sorry, {product.name} only has {product.stock_quantity} units left in stock.")
                    product.stock_quantity -= item.quantity
                    if product.stock_quantity == 0:
                        product.is_available = False
                    product.save()
                
                # Save transaction and provider info
                order.payment_status = Order.PaymentStatusChoices.PAID
                order.transaction_id = data.get('reference')
                
                authorization = data.get('authorization', {})
                order.momo_provider = authorization.get('brand', 'Paystack')  # MTN, Telecel, Visa, etc.
                order.momo_number = authorization.get('last4', 'N/A')  # Masked card last4 or wallet number suffix
                order.save()
                
                # Clear Cart
                cart = Cart.objects.filter(user=order.user).first() if order.user else None
                if cart:
                    cart.items.all().delete()
                    
            # Send Email
            send_order_confirmation_email(order, order.user.email if order.user else "buyer@example.com")
            
            messages.success(request, "Payment verified and order placed successfully!")
            return redirect('order_success', order_number=order.order_number)
            
        else:
            error_msg = response_data.get('message', 'Verification failed.')
            messages.error(request, f"Payment Verification Failed: {error_msg}")
            return redirect('checkout')
            
    except ValueError as ve:
        messages.error(request, str(ve))
        return redirect('checkout')
    except Exception as e:
        messages.error(request, f"An error occurred during payment verification: {str(e)}")
        return redirect('checkout')

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
