from django.contrib import admin
from .models import Category, Product, ContactMessage, ProductImage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'farmer', 'category', 'price', 'unit', 'stock_quantity', 'is_available', 'is_featured', 'created_at']
    list_filter = ['category', 'is_available', 'is_featured', 'farmer__region']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description', 'farmer__farm_name']
    ordering = ['-created_at']

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'full_name', 'email', 'phone', 'created_at']
    search_fields = ['full_name', 'email', 'subject', 'message']
    ordering = ['-created_at']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image', 'order', 'created_at']
    list_filter = ['product']
    readonly_fields = ['created_at']
