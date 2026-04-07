from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Family, Badge


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ['name', 'invite_code', 'currency_symbol', 'created_at']
    readonly_fields = ['invite_code']


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'role', 'family', 'total_points', 'avatar']
    list_filter = ['role', 'family']
    fieldsets = UserAdmin.fieldsets + (
        ('Family Info', {'fields': ('family', 'role', 'avatar', 'date_of_birth', 'total_points', 'total_earned_lifetime')}),
    )


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge_type', 'awarded_at']
