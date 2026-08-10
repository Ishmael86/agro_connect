from django import forms
from .models import Order
from farmers.models import GHANA_REGIONS

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'delivery_address', 'region', 'city', 'payment_method']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name',
                'id': 'id_full_name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number',
                'id': 'id_phone'
            }),
            'delivery_address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your delivery address',
                'rows': 3,
                'id': 'id_delivery_address'
            }),
            'region': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_region'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter city/town',
                'id': 'id_city'
            }),
            'payment_method': forms.RadioSelect(attrs={
                'class': 'payment-method-radio'
            })
        }
