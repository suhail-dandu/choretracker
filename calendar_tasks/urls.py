from django.urls import path
from . import views

app_name = 'calendar_tasks'

urlpatterns = [
    # Calendar views
    path('', views.calendar_view, name='calendar_view'),
    path('<int:year>/<int:month>/<int:day>/', views.calendar_day_detail, name='calendar_day_detail'),

    # Task management
    path('task/create/', views.create_calendar_task, name='create_calendar_task'),
    path('task/<int:task_id>/edit/', views.edit_calendar_task, name='edit_calendar_task'),
    path('task/<int:task_id>/delete/', views.delete_calendar_task, name='delete_calendar_task'),
    path('task/<int:task_id>/complete/', views.task_complete, name='task_complete'),

    # Task approval
    path('approvals/', views.pending_task_approvals, name='pending_task_approvals'),
    path('task/<int:task_id>/approve/', views.task_approve, name='task_approve'),
    path('task/<int:task_id>/reject/', views.task_reject, name='task_reject'),
    path('assignment/<int:assignment_id>/approve/', views.assignment_approve, name='assignment_approve'),
    path('assignment/<int:assignment_id>/reject/', views.assignment_reject, name='assignment_reject'),

    # Recurring templates
    path('recurring/', views.recurring_templates_list, name='recurring_templates_list'),
    path('recurring/create/', views.create_recurring_template, name='create_recurring_template'),
    path('recurring/<int:template_id>/edit/', views.edit_recurring_template, name='edit_recurring_template'),
    path('recurring/<int:template_id>/delete/', views.delete_recurring_template, name='delete_recurring_template'),

    # Schedule patterns
    path('patterns/', views.schedule_patterns_list, name='schedule_patterns_list'),
    path('patterns/create/', views.create_schedule_pattern, name='create_schedule_pattern'),
    path('patterns/<int:pattern_id>/edit/', views.edit_schedule_pattern, name='edit_schedule_pattern'),
    path('patterns/<int:pattern_id>/delete/', views.delete_schedule_pattern, name='delete_schedule_pattern'),

    # Bad deeds
    path('bad-deeds/', views.bad_deeds_list, name='bad_deeds_list'),
    path('bad-deeds/create/', views.create_bad_deed, name='create_bad_deed'),
    path('bad-deeds/<int:bad_deed_id>/edit/', views.edit_bad_deed, name='edit_bad_deed'),
    path('bad-deeds/<int:bad_deed_id>/delete/', views.delete_bad_deed, name='delete_bad_deed'),
    path('bad-deeds/instances/', views.bad_deeds_instances, name='bad_deeds_instances'),
    path('bad-deeds/add/', views.add_bad_deed_instance, name='add_bad_deed_instance'),
    path('bad-deeds/add/<int:child_id>/', views.add_bad_deed_instance, name='add_bad_deed_instance_child'),
    path('bad-deeds/<int:instance_id>/remove/', views.remove_bad_deed, name='remove_bad_deed'),
]
