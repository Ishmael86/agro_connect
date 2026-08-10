from django import forms
from django.contrib.auth import get_user_model
from farmers.models import GHANA_REGIONS

User = get_user_model()

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username or email',
            'id': 'id_username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'id_password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'remember_me'
        })
    )

class RegistrationForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
            'id': 'id_full_name'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'id': 'id_confirm_password'
        })
    )
    
    # Farmer specific fields
    farm_name = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your farm name',
            'id': 'id_farm_name'
        })
    )
    region = forms.ChoiceField(
        required=False,
        choices=[('', 'Select your region')] + GHANA_REGIONS,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_region'
        })
    )
    location = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter farm location',
            'id': 'id_location'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'account_type', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username', 'id': 'id_username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address', 'id': 'id_email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number', 'id': 'id_phone'}),
            'account_type': forms.RadioSelect(attrs={'class': 'account-type-radio', 'id': 'id_account_type'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password', 'id': 'id_password'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        account_type = cleaned_data.get("account_type")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        if account_type == User.AccountType.FARMER:
            farm_name = cleaned_data.get("farm_name")
            region = cleaned_data.get("region")
            location = cleaned_data.get("location")

            if not farm_name:
                self.add_error('farm_name', "Farm name is required for farmers.")
            if not region:
                self.add_error('region', "Region is required for farmers.")
            if not location:
                self.add_error('location', "Location is required for farmers.")
        return cleaned_data

from .models import Address
from payments.models import PaymentMethod
from products.models import Review

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['label', 'full_name', 'phone', 'region', 'city', 'address', 'additional_information', 'is_default']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Home, Office'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipient Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipient Phone'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City / District'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Street Address / Landmarks'}),
            'additional_information': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Delivery instructions...'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['payment_type', 'provider', 'masked_reference', 'is_default']
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'provider': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MTN, Telecel, Visa'}),
            'masked_reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. **** 1234'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.HiddenInput(attrs={'id': 'id_rating_value'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your review here...'}),
        }

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profile_image = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
