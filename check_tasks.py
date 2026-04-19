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
    print(f"User: {user.username}, Family: {user.family}")

    # Get current date
    current_date = timezone.now().date()
    print(f"Today: {current_date}")

    # Calculate first and last day of month
    first_day = current_date.replace(day=1)
    if current_date.month == 12:
        last_day = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)

    print(f"Month range: {first_day} to {last_day}")

    # Get tasks
    tasks = CalendarTask.objects.filter(
        family=user.family,
        scheduled_date__range=[first_day, last_day]
    )
    print(f"Tasks in month: {tasks.count()}")
    for task in tasks:
        print(f"  - {task.title} on {task.scheduled_date}")

    # Check all tasks
    all_tasks = CalendarTask.objects.filter(family=user.family)
    print(f"\nAll tasks in family: {all_tasks.count()}")
    for task in all_tasks:
        print(f"  - {task.title} on {task.scheduled_date}")

