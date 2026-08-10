from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'phone', 'account_type', 'is_staff', 'date_joined']
    fieldsets = UserAdmin.fieldsets + (
        ('AgroConnect Info', {'fields': ('account_type', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('AgroConnect Info', {'fields': ('account_type', 'phone')}),
    )

admin.site.register(User, CustomUserAdmin)
