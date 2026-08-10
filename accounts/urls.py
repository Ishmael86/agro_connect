from django.urls import path
from . import views
from . import buyer_views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Buyer Dashboard URLs
    path('buyer/', buyer_views.buyer_dashboard, name='buyer_dashboard'),
    path('buyer/orders/', buyer_views.buyer_orders, name='buyer_orders'),
    path('buyer/orders/<str:order_number>/', buyer_views.buyer_order_detail, name='buyer_order_detail'),
    path('buyer/cart/', buyer_views.buyer_cart, name='buyer_cart'),
    path('buyer/checkout/', buyer_views.buyer_checkout, name='buyer_checkout'),
    path('buyer/wishlist/', buyer_views.buyer_wishlist, name='buyer_wishlist'),
    path('buyer/addresses/', buyer_views.buyer_addresses, name='buyer_addresses'),
    path('buyer/payments/', buyer_views.buyer_payments, name='buyer_payments'),
    path('buyer/reviews/', buyer_views.buyer_reviews, name='buyer_reviews'),
    path('buyer/messages/', buyer_views.buyer_messages, name='buyer_messages'),
    path('buyer/notifications/', buyer_views.buyer_notifications, name='buyer_notifications'),
    path('buyer/settings/', buyer_views.buyer_settings, name='buyer_settings'),
    path('buyer/profile/', buyer_views.buyer_profile, name='buyer_profile'),
    path('buyer/change-password/', buyer_views.buyer_change_password, name='buyer_change_password'),
    path('buyer/help/', buyer_views.buyer_help, name='buyer_help'),
    path('buyer/orders/<str:order_number>/invoice/', buyer_views.buyer_download_invoice, name='buyer_download_invoice'),
]
