from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .forms import LoginForm, RegistrationForm
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
                return redirect('home')
            else:
                messages.error(request, "Invalid username/email or password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Save the user (inactive/active)
                user = form.save(commit=False)
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

                # Log the user in directly after registering
                login(request, user)
                
                # Merge guest cart
                guest_cart_id = request.session.get('cart_id')
                if guest_cart_id:
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

                messages.success(request, "Registration successful! Welcome to AgroConnect.")
                return redirect('home')
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
    
    # 1. Superuser Check: redirect administrator to admin panel
    if user.is_superuser:
        return redirect('/admin/')
        
    # 2. Buyer Check: redirect buyer to full-featured buyer dashboard
    if user.account_type == 'BUYER':
        return redirect('buyer_dashboard')
        
    # 3. Farmer Dashboard: redirect to the new farmer dashboard
    if user.account_type == 'FARMER':
        return redirect('farmer_dashboard')
        
    return render(request, 'accounts/dashboard.html', {})
