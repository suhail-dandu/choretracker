#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from calendar_tasks.models import CalendarTask
from datetime import datetime, timedelta
from accounts.models import User
from django.utils import timezone
from django.template.loader import render_to_string

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

    # Group tasks by date - using isoformat as the key (matching the view)
    tasks_by_date = {}
    for task in tasks:
        date_key = task.scheduled_date.isoformat()
        if date_key not in tasks_by_date:
            tasks_by_date[date_key] = []
        tasks_by_date[date_key].append(task)

    print(f"Tasks by date: {tasks_by_date}")
    print()

    # Test the date formatting
    test_date = current_date.replace(day=13)  # The date of our test task
    print(f"Test date: {test_date}")
    print(f"  isoformat(): {test_date.isoformat()}")
    print(f"  |date:'Y-m-d' format: {test_date.strftime('%Y-%m-%d')}")
    print(f"  Match? {test_date.isoformat() == test_date.strftime('%Y-%m-%d')}")
    print()

    # Now check if tasks show up
    for date_key in tasks_by_date.keys():
        print(f"Task on {date_key}:")
        for task in tasks_by_date[date_key]:
            print(f"  - {task.title}")

