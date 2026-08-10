from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'farmer', 'quantity', 'unit_price', 'subtotal']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'phone', 'region', 'city', 'payment_method', 'total', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'region', 'created_at']
    search_fields = ['order_number', 'full_name', 'phone', 'city']
    readonly_fields = ['order_number', 'subtotal', 'delivery_fee', 'total', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    ordering = ['-created_at']
