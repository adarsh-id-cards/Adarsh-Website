from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SystemSettings, ActivityLog

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for User model"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'role')}),
    )

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'updated_at')
    search_fields = ('key', 'description')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'description', 'target_model', 'created_at')
    list_filter = ('action', 'target_model', 'created_at')
