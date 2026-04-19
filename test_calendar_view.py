#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from calendar_tasks.models import CalendarTask
from datetime import datetime, timedelta
from accounts.models import User
from django.utils import timezone

# Get the test user
user = User.objects.filter(username='zaid_dandu').first()
if user:
    # Get current date
    current_date = timezone.now().date()
    
    # Calculate first and last day of month
    first_day = current_date.replace(day=1)
    if current_date.month == 12:
        last_day = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
    
    tasks = CalendarTask.objects.filter(
        family=user.family,
        scheduled_date__range=[first_day, last_day]
    )
    
    if user.is_child:
        tasks = tasks.filter(assigned_to=user)
    
    # Group tasks by date
    tasks_by_date = {}
    for task in tasks:
        date_key = task.scheduled_date.isoformat()
        if date_key not in tasks_by_date:
            tasks_by_date[date_key] = []
        tasks_by_date[date_key].append(task)
    
    print("tasks_by_date dict:")
    print(tasks_by_date)
    print()
    
    # Test the template logic
    import calendar as cal_module
    month_calendar = cal_module.monthcalendar(current_date.year, current_date.month)
    print(f"Month calendar: {month_calendar}")
    print()
    
    # Generate calendar days
    calendar_days = []
    
    # Add days from previous month to fill the first week
    if month_calendar[0][0] != 1:
        prev_month_date = first_day - timedelta(days=1)
        last_day_prev_month = cal_module.monthrange(prev_month_date.year, prev_month_date.month)[1]
        start_day = last_day_prev_month - month_calendar[0][0] + 1
        for day in range(start_day, last_day_prev_month + 1):
            calendar_days.append(prev_month_date.replace(day=day))
    
    # Add days from current month
    for week in month_calendar:
        for day_num in week:
            if day_num != 0:
                calendar_days.append(current_date.replace(day=day_num))
    
    # Add days from next month to fill the last week
    remaining_days = 42 - len(calendar_days)
    if remaining_days > 0:
        for day in range(1, remaining_days + 1):
            if current_date.month == 12:
                next_month_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                next_month_date = current_date.replace(month=current_date.month + 1)
            calendar_days.append(next_month_date.replace(day=day))
    
    print(f"Calendar days (first 10): {calendar_days[:10]}")
    print()
    
    # Test matching logic
    all_tasks_items = list(tasks_by_date.items())
    print(f"all_tasks_items: {all_tasks_items}")
    print()
    
    # Simulate the template loop
    for day in calendar_days[:15]:  # Just first 15 days
        day_iso = day.isoformat()
        print(f"Day {day} (iso: {day_iso}):")
        for date_str, task_list in all_tasks_items:
            if date_str == day_iso:
                print(f"  Match found! Tasks: {[t.title for t in task_list]}")
            else:
                print(f"  No match: {date_str} != {day_iso}")

