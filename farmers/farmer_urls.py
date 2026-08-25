from django.urls import path
from . import farmer_views

urlpatterns = [
    path('', farmer_views.farmer_dashboard, name='farmer_dashboard'),
    path('products/', farmer_views.farmer_products, name='farmer_products'),
    path('products/add/', farmer_views.farmer_add_product, name='farmer_add_product'),
    path('products/<slug:slug>/edit/', farmer_views.farmer_edit_product, name='farmer_edit_product'),
    path('products/<slug:slug>/delete/', farmer_views.farmer_delete_product, name='farmer_delete_product'),
    path('orders/', farmer_views.farmer_orders, name='farmer_orders'),
    path('orders/<str:order_number>/', farmer_views.farmer_order_detail, name='farmer_order_detail'),
    path('earnings/', farmer_views.farmer_earnings, name='farmer_earnings'),
    path('payouts/', farmer_views.farmer_payouts, name='farmer_payouts'),
    path('customers/', farmer_views.farmer_customers, name='farmer_customers'),
    path('customers/<int:user_id>/', farmer_views.farmer_customer_detail, name='farmer_customer_detail'),
    path('messages/', farmer_views.farmer_messages, name='farmer_messages'),
    path('reviews/', farmer_views.farmer_reviews, name='farmer_reviews'),
    path('profile/', farmer_views.farmer_profile, name='farmer_profile'),
    path('settings/', farmer_views.farmer_settings, name='farmer_settings'),
    path('notifications/', farmer_views.farmer_notifications, name='farmer_notifications'),
    path('support/', farmer_views.farmer_support, name='farmer_support'),
    path('support/ticket/<int:ticket_id>/', farmer_views.farmer_ticket_detail, name='farmer_ticket_detail'),
]
