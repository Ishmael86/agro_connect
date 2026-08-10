from django.contrib import admin
from .models import FarmerProfile

@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ['farm_name', 'user', 'region', 'location', 'verified', 'rating', 'created_at']
    list_filter = ['region', 'verified']
    search_fields = ['farm_name', 'user__username', 'user__email', 'location']
    ordering = ['-created_at']
