from django.contrib import admin
from .models import RecurringChoreTemplate, SchedulePattern, CalendarTask, BadDeed, BadDeedInstance


@admin.register(RecurringChoreTemplate)
class RecurringChoreTemplateAdmin(admin.ModelAdmin):
    list_display = ('chore_title', 'family', 'assigned_to', 'frequency', 'is_active', 'created_at')
    list_filter = ('family', 'frequency', 'is_active', 'created_at')
    search_fields = ('chore_title', 'assigned_to__first_name')
    readonly_fields = ('created_at', 'last_generated')
    fieldsets = (
        ('Basic Info', {'fields': ('family', 'chore_title', 'chore_description', 'points', 'category')}),
        ('Recurrence', {'fields': ('frequency', 'days_of_week', 'day_of_month', 'scheduled_time')}),
        ('Assignment', {'fields': ('assigned_to', 'created_by')}),
        ('Control', {'fields': ('is_active', 'start_date', 'end_date')}),
        ('Metadata', {'fields': ('created_at', 'last_generated'), 'classes': ('collapse',)}),
    )


@admin.register(SchedulePattern)
class SchedulePatternAdmin(admin.ModelAdmin):
    list_display = ('name', 'family', 'pattern_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('family', 'pattern_type', 'is_active', 'start_date')
    search_fields = ('name', 'family__name')
    date_hierarchy = 'start_date'


@admin.register(CalendarTask)
class CalendarTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'family', 'assigned_to', 'scheduled_date', 'status', 'points')
    list_filter = ('family', 'status', 'category', 'scheduled_date')
    search_fields = ('title', 'assigned_to__first_name')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'approved_at')
    date_hierarchy = 'scheduled_date'
    fieldsets = (
        ('Basic Info', {'fields': ('family', 'title', 'description', 'points', 'category')}),
        ('Schedule', {'fields': ('scheduled_date', 'scheduled_time', 'due_time')}),
        ('Assignment', {'fields': ('assigned_to', 'created_by', 'recurring_template')}),
        ('Status', {'fields': ('status', 'note', 'rejection_reason')}),
        ('Approval', {'fields': ('approved_by', 'completed_at', 'approved_at')}),
        ('Metadata', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(BadDeed)
class BadDeedAdmin(admin.ModelAdmin):
    list_display = ('title', 'family', 'assigned_to', 'negative_points', 'is_active', 'is_recurring')
    list_filter = ('family', 'is_active', 'is_recurring', 'category', 'created_at')
    search_fields = ('title', 'assigned_to__first_name')
    readonly_fields = ('created_at', 'last_applied')
    fieldsets = (
        ('Basic Info', {'fields': ('family', 'title', 'description', 'negative_points', 'category')}),
        ('Recurrence', {'fields': ('is_recurring', 'frequency', 'days_of_week', 'day_of_month', 'scheduled_time')}),
        ('Assignment', {'fields': ('assigned_to', 'created_by')}),
        ('Control', {'fields': ('is_active', 'start_date', 'end_date')}),
        ('Metadata', {'fields': ('created_at', 'last_applied'), 'classes': ('collapse',)}),
    )


@admin.register(BadDeedInstance)
class BadDeedInstanceAdmin(admin.ModelAdmin):
    list_display = ('title', 'family', 'assigned_to', 'negative_points', 'status', 'created_date')
    list_filter = ('family', 'status', 'category', 'created_date')
    search_fields = ('title', 'assigned_to__first_name', 'reason')
    readonly_fields = ('created_at', 'created_date')
    fieldsets = (
        ('Incident Info', {'fields': ('family', 'title', 'description', 'negative_points', 'category', 'reason')}),
        ('Assignment', {'fields': ('assigned_to', 'created_by')}),
        ('Status', {'fields': ('status', 'bad_deed')}),
        ('Removal', {'fields': ('removed_by', 'removed_at'), 'classes': ('collapse',)}),
        ('Metadata', {'fields': ('created_at', 'created_date'), 'classes': ('collapse',)}),
    )
