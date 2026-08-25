from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('how-it-works/', views.how_it_works_view, name='how_it_works'),
    path('products/', views.product_list_view, name='product_list'),
    path('products/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('categories/', views.category_list_view, name='category_list'),
    path('search/', views.search_view, name='search'),
    path('privacy-policy/', views.public_page_view, {'slug': 'privacy-policy'}, name='privacy_policy'),
    path('terms-of-service/', views.public_page_view, {'slug': 'terms-of-service'}, name='terms_of_service'),
    path('faqs/', views.public_page_view, {'slug': 'faqs'}, name='faqs'),
]
