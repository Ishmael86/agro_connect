from django.urls import path
from . import views

urlpatterns = [
    path('', views.farmer_list_view, name='farmer_list'),
    path('<int:id>/', views.farmer_detail_view, name='farmer_detail'),
]
