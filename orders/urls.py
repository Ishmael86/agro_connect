from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/paystack/callback/', views.paystack_callback_view, name='paystack_callback'),
    path('order/success/<str:order_number>/', views.order_success_view, name='order_success'),
]
