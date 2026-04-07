from django.contrib import admin
from .models import Chore, ChoreAssignment, PointTransaction, PocketMoneyPayout


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ['title', 'family', 'points', 'category', 'is_active', 'created_by']
    list_filter = ['family', 'category', 'is_active']
    search_fields = ['title']


@admin.register(ChoreAssignment)
class ChoreAssignmentAdmin(admin.ModelAdmin):
    list_display = ['chore', 'assigned_to', 'status', 'due_date', 'points_awarded']
    list_filter = ['status', 'chore__family']
    list_editable = ['status']


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'points', 'balance_after', 'reason', 'created_at', 'created_by']
    list_filter = ['user__family']
    readonly_fields = ['created_at']


@admin.register(PocketMoneyPayout)
class PocketMoneyPayoutAdmin(admin.ModelAdmin):
    list_display = ['kid', 'amount_euros', 'points_at_payout', 'month', 'paid_by', 'paid_at']
    list_filter = ['kid__family', 'month']
