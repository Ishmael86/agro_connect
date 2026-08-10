from django import forms
from django.contrib.auth import get_user_model
from .models import SiteSettings, Promotion, SupportTicket, SupportTicketMessage
from products.models import Category, Product
from orders.models import Order
from farmers.models import FarmerProfile, Payout

User = get_user_model()

class AdminUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'account_type', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'phone': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'account_type': forms.Select(attrs={'class': 'form-select rounded-pill px-3'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Category Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3, 'placeholder': 'Category Description'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control rounded-pill'}),
        }

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select rounded-pill px-3'}),
        }

class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ['title', 'description', 'image', 'discount_percentage', 'start_date', 'end_date', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'step': '0.01'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control rounded-pill px-3', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control rounded-pill px-3', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control rounded-pill'}),
        }

class SettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'site_email', 'site_phone', 'currency', 'timezone',
            'site_description', 'commission_rate', 'maintenance_mode',
            'momo_api_url', 'bank_transfer_enabled',
            'smtp_host', 'smtp_port', 'smtp_user', 'smtp_password',
            'sms_api_key', 'sms_sender_id',
            'seo_title', 'seo_keywords', 'seo_description'
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'site_email': forms.EmailInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'site_phone': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'currency': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'timezone': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'site_description': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3}),
            'commission_rate': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'step': '0.01'}),
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'momo_api_url': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'bank_transfer_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'smtp_host': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'smtp_user': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'smtp_password': forms.PasswordInput(attrs={'class': 'form-control rounded-pill px-3', 'render_value': True}),
            'sms_api_key': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'sms_sender_id': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'seo_title': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'seo_keywords': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'seo_description': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3}),
        }

class SupportTicketReplyForm(forms.ModelForm):
    class Meta:
        model = SupportTicketMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 4, 'placeholder': 'Type your official administrative reply...'}),
        }

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'phone': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
        }
