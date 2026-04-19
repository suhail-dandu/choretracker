#!/usr/bin/env python
"""
Comprehensive test to verify calendar tasks display correctly.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from calendar_tasks.models import CalendarTask
from datetime import datetime, timedelta, date
from accounts.models import User
from django.utils import timezone

print("=" * 60)
print("CALENDAR TASK DISPLAY TEST")
print("=" * 60)

# 1. Check database for tasks
print("\n1. Database Check:")
all_tasks = CalendarTask.objects.all()
print(f"   Total tasks in database: {all_tasks.count()}")
for task in all_tasks:
    print(f"   - {task.title} on {task.scheduled_date} for {task.assigned_to.display_name}")

# 2. Check if any recurring templates exist
from calendar_tasks.models import RecurringChoreTemplate
templates = RecurringChoreTemplate.objects.filter(is_active=True)
print(f"\n2. Recurring Templates Check:")
print(f"   Active templates: {templates.count()}")
for t in templates:
    print(f"   - {t.chore_title} ({t.frequency}) for {t.assigned_to.display_name}")

# 3. Simulate calendar view for a child user
print(f"\n3. Calendar View Simulation:")
user = User.objects.filter(role='child').first()
if user:
    print(f"   Testing with user: {user.username}")

    current_date = timezone.now().date()
    first_day = current_date.replace(day=1)
    if current_date.month == 12:
        last_day = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)

    print(f"   Date range: {first_day} to {last_day}")

    # Query tasks like the view does
    tasks = CalendarTask.objects.filter(
        family=user.family,
        scheduled_date__range=[first_day, last_day]
    )

    if user.is_child:
        tasks = tasks.filter(assigned_to=user)

    print(f"   Tasks in month: {tasks.count()}")

    # Group by date
    tasks_by_date = {}
    for task in tasks:
        date_key = task.scheduled_date.isoformat()
        if date_key not in tasks_by_date:
            tasks_by_date[date_key] = []
        tasks_by_date[date_key].append(task)

    print(f"   Unique dates with tasks: {len(tasks_by_date)}")

    # Test template date matching
    print(f"\n   Template Matching Test:")
    import calendar as cal_module
    month_calendar = cal_module.monthcalendar(current_date.year, current_date.month)

    # Generate first few days for testing
    test_days = []
    for week in month_calendar:
        for day_num in week:
            if day_num != 0:
                test_days.append(current_date.replace(day=day_num))
            if len(test_days) >= 20:
                break
        if len(test_days) >= 20:
            break

    matches = 0
    for day in test_days:
        day_formatted = day.strftime('%Y-%m-%d')
        if day_formatted in tasks_by_date:
            matches += 1
            print(f"   ✓ Match on {day_formatted}: {len(tasks_by_date[day_formatted])} task(s)")

    print(f"   Total matches: {matches}/{len(test_days)} test days")
else:
    print("   No child user found!")

# 4. Check template syntax
print(f"\n4. Template Syntax Check:")
from django.template.loader import render_to_string
try:
    # Test rendering the calendar template with test data
    test_context = {
        'current_date': timezone.now().date(),
        'calendar_days': [timezone.now().date() + timedelta(days=i) for i in range(7)],
        'all_tasks_items': [],
        'tasks_by_date': {},
        'prev_month': (timezone.now().date().replace(day=1) - timedelta(days=1)).replace(day=1),
        'next_month': (timezone.now().date().replace(day=1) + timedelta(days=31)).replace(day=1),
        'month_str': timezone.now().date().strftime('%Y-%m'),
        'user': User.objects.first(),
    }

    html = render_to_string('calendar_tasks/calendar_view.html', test_context)
    print("   ✓ Template renders successfully")
    print(f"   HTML length: {len(html)} bytes")
except Exception as e:
    print(f"   ✗ Template rendering failed: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)

