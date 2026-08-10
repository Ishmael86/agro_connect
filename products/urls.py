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
]
