from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
import logging
from django.urls import reverse

logger = logging.getLogger(__name__)
from .forms import LoginForm, RegistrationForm
from .models import Wishlist
from farmers.models import FarmerProfile
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from products.models import Product

User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data['remember_me']

            # Support logging in with email or username
            user = None
            if '@' in username:
                user_obj = User.objects.filter(email=username).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
            else:
                user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                
                # Configure session expiry if remember me is not checked
                if not remember_me:
                    request.session.set_expiry(0) # expires when browser closes
                else:
                    request.session.set_expiry(1209600) # 2 weeks

                # Merge guest cart with user cart
                guest_cart_id = request.session.get('cart_id')
                if guest_cart_id:
                    with transaction.atomic():
                        guest_cart = Cart.objects.filter(id=guest_cart_id).first()
                        if guest_cart:
                            user_cart, created = Cart.objects.get_or_create(user=user)
                            # Transfer or merge items
                            for item in guest_cart.items.all():
                                existing_item = user_cart.items.filter(product=item.product).first()
                                if existing_item:
                                    existing_item.quantity += item.quantity
                                    # Ensure it doesn't exceed stock
                                    if existing_item.quantity > item.product.stock_quantity:
                                        existing_item.quantity = item.product.stock_quantity
                                    existing_item.save()
                                else:
                                    item.cart = user_cart
                                    item.save()
                            # Delete the guest cart
                            guest_cart.delete()
                            request.session.pop('cart_id', None)

                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                
                # Role-based direct dashboard routing - only Admin goes direct
                if user.is_superuser or user.is_staff:
                    return redirect('admin_dashboard')
                if user.account_type == 'FARMER':
                    return redirect('farmer_dashboard')
                return redirect('home')
            else:
                # Check if account exists but is inactive
                inactive_user = None
                if '@' in username:
                    inactive_user = User.objects.filter(email=username, is_active=False).first()
                else:
                    inactive_user = User.objects.filter(username=username, is_active=False).first()
                
                if inactive_user and inactive_user.check_password(password):
                    if inactive_user.is_suspended:
                        messages.error(request, "Your account has been suspended by the administrator. Please contact support.")
                        return render(request, 'accounts/login.html', {
                            'form': form,
                            'show_resend_link': False
                        })
                    else:
                        messages.error(request, "Your account is not active. Please check your email for the activation link.")
                        return render(request, 'accounts/login.html', {
                            'form': form,
                            'show_resend_link': True,
                            'email': inactive_user.email
                        })
                else:
                    messages.error(request, "Invalid username/email or password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def send_activation_email(request, user):
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    activation_link = request.build_absolute_uri(
        reverse('activate', kwargs={'uidb64': uidb64, 'token': token})
    )
    
    subject = "Verify your AgroConnect Account"
    message_body = (
        f"Hello {user.first_name or user.username},\n\n"
        f"Thank you for registering on AgroConnect!\n\n"
        f"Please click the link below to verify your email address and activate your account:\n"
        f"{activation_link}\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"Best regards,\nThe AgroConnect Team"
    )
    try:
        send_mail(
            subject,
            message_body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )
    except Exception as e:
        logger.error(f"Failed to send account activation email to {user.email}: {e}")

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Save the user as inactive until email is verified
                user = form.save(commit=False)
                user.is_active = False
                
                # Split full_name into first and last name
                full_name = form.cleaned_data['full_name']
                names = full_name.split(' ', 1)
                user.first_name = names[0]
                if len(names) > 1:
                    user.last_name = names[1]
                
                # Hash the password
                user.set_password(form.cleaned_data['password'])
                user.save()

                # If Farmer, create FarmerProfile
                if user.account_type == User.AccountType.FARMER:
                    FarmerProfile.objects.create(
                        user=user,
                        farm_name=form.cleaned_data['farm_name'],
                        phone=form.cleaned_data['phone'],
                        region=form.cleaned_data['region'],
                        location=form.cleaned_data['location'],
                        verified=False
                    )

                # Send activation email
                send_activation_email(request, user)

                messages.success(request, "Registration successful! Please check your email to activate your account.")
                return redirect('activation_sent')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')

@login_required
def dashboard_view(request):
    user = request.user
    
    # 1. Staff or Superuser Check: redirect administrator to custom admin panel
    if user.is_superuser or user.is_staff:
        return redirect('admin_dashboard')
        
    # 2. Buyer Check: redirect buyer to full-featured buyer dashboard
    if user.account_type == 'BUYER':
        return redirect('buyer_dashboard')
        
    # 3. Farmer Dashboard: redirect to the new farmer dashboard
    if user.account_type == 'FARMER':
        return redirect('farmer_dashboard')
        
    return render(request, 'accounts/dashboard.html', {})


@require_POST
@login_required
def ajax_toggle_wishlist(request):
    """AJAX endpoint to add/remove a product from the user's wishlist."""
    product_id = request.POST.get('product_id')
    if not product_id:
        return JsonResponse({'success': False, 'message': 'No product specified.'}, status=400)
    
    product = get_object_or_404(Product, id=product_id)
    
    wish, created = Wishlist.objects.get_or_create(buyer=request.user, product=product)
    if not created:
        wish.delete()
        return JsonResponse({
            'success': True,
            'status': 'removed',
            'message': f'{product.name} removed from wishlist.'
        })
    return JsonResponse({
        'success': True,
        'status': 'added',
        'message': f'{product.name} added to wishlist.'
    })

def activation_sent_view(request):
    return render(request, 'accounts/activation_sent.html')

def activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if user.is_suspended:
            messages.error(request, "This account is suspended and cannot be activated.")
            return redirect('login')
        user.is_active = True
        user.save()
        login(request, user)
        
        # Merge guest cart
        guest_cart_id = request.session.get('cart_id')
        if guest_cart_id:
            with transaction.atomic():
                guest_cart = Cart.objects.filter(id=guest_cart_id).first()
                if guest_cart:
                    user_cart, created = Cart.objects.get_or_create(user=user)
                    for item in guest_cart.items.all():
                        existing_item = user_cart.items.filter(product=item.product).first()
                        if existing_item:
                            existing_item.quantity += item.quantity
                            if existing_item.quantity > item.product.stock_quantity:
                                existing_item.quantity = item.product.stock_quantity
                            existing_item.save()
                        else:
                            item.cart = user_cart
                            item.save()
                    guest_cart.delete()
                    request.session.pop('cart_id', None)

        messages.success(request, f"Your email has been verified! Welcome to AgroConnect, {user.first_name or user.username}.")
        if user.is_superuser or user.is_staff:
            return redirect('admin_dashboard')
        if user.account_type == 'FARMER':
            return redirect('farmer_dashboard')
        return redirect('home')
    else:
        messages.error(request, "The activation link is invalid or expired. Please request a new one.")
        return redirect('login')

def resend_activation_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            user = User.objects.filter(email=email, is_active=False).first()
            if user:
                if user.is_suspended:
                    messages.error(request, "This account is suspended and cannot be activated.")
                    return redirect('login')
                send_activation_email(request, user)
                messages.success(request, "A new activation link has been sent to your email.")
                return redirect('activation_sent')
            else:
                messages.warning(request, "This email is either already verified or not registered.")
                return redirect('login')
        else:
            messages.error(request, "Please enter a valid email address.")
    
    email_initial = request.GET.get('email', '')
    return render(request, 'accounts/resend_activation.html', {'email': email_initial})
