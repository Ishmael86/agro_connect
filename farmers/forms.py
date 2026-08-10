from django import forms
from .models import FarmerProfile, Payout, FarmerNotificationSetting
from products.models import Product, Category, ContactMessage

class FarmerProfileForm(forms.ModelForm):
    class Meta:
        model = FarmerProfile
        fields = ['farm_name', 'profile_image', 'cover_image', 'phone', 'region', 'district', 'location', 'description']
        widgets = {
            'farm_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'phone': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'region': forms.Select(attrs={'class': 'form-select rounded-pill px-3'}),
            'district': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'location': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 4}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control rounded-pill'}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control rounded-pill'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'discount_price', 'unit', 'stock_quantity', 'location', 'main_image', 'is_available', 'is_featured']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Fresh Tomatoes'}),
            'category': forms.Select(attrs={'class': 'form-select rounded-pill px-3'}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 4, 'placeholder': 'Describe your crop quality, freshness...'}),
            'price': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'min': '0', 'step': '0.01'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'min': '0', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. kg, crate, bunch'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'min': '0'}),
            'location': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Eastern Region Farm'}),
            'main_image': forms.ClearableFileInput(attrs={'class': 'form-control rounded-pill'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PayoutRequestForm(forms.ModelForm):
    class Meta:
        model = Payout
        fields = ['amount', 'payment_method', 'account_number', 'account_name', 'bank_name']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'min': '1', 'step': '0.01', 'placeholder': 'GHS 10.00'}),
            'payment_method': forms.Select(attrs={'class': 'form-select rounded-pill px-3'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Momo Phone or Bank Account Number'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Full Name on Account'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Required for Bank Transfer'}),
        }

class FarmerNotificationSettingsForm(forms.ModelForm):
    class Meta:
        model = FarmerNotificationSetting
        fields = ['new_order', 'order_status', 'new_message', 'new_review', 'payout', 'promotions']
        widgets = {
            'new_order': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'new_message': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'new_review': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payout': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'promotions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SupportForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['full_name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Your Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'name@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. +233 24 123 4567'}),
            'subject': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'How can we help you?'}),
            'message': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 4, 'placeholder': 'Provide detail context of your issue...'}),
        }
