#!/usr/bin/env python
"""
Deep diagnostic of calendar tasks issue.
Checks database, view logic, and template rendering.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from calendar_tasks.models import CalendarTask, RecurringChoreTemplate
from accounts.models import User, Family
from django.utils import timezone
from datetime import date, timedelta

print("\n" + "="*80)
print("DEEP DIAGNOSTIC - CALENDAR TASKS ISSUE")
print("="*80)

# 1. Check all tasks in database
print("\n1. ALL TASKS IN DATABASE:")
print("-" * 80)
all_tasks = CalendarTask.objects.all().order_by('scheduled_date')
print(f"Total tasks: {all_tasks.count()}")
for task in all_tasks:
    print(f"  • {task.title}")
    print(f"    Date: {task.scheduled_date} | Family: {task.family} | Child: {task.assigned_to}")

# 2. Check recurring templates
print("\n2. RECURRING TEMPLATES:")
print("-" * 80)
templates = RecurringChoreTemplate.objects.all()
print(f"Total templates: {templates.count()}")
for t in templates:
    print(f"  • {t.chore_title} ({t.frequency}) for {t.assigned_to.display_name}")
    print(f"    Active: {t.is_active} | Start: {t.start_date} | End: {t.end_date}")

# 3. Check generated tasks from templates
print("\n3. TASKS GENERATED FROM TEMPLATES:")
print("-" * 80)
generated = CalendarTask.objects.filter(recurring_template__isnull=False)
print(f"Total generated tasks: {generated.count()}")
for task in generated:
    print(f"  • {task.title} on {task.scheduled_date}")

# 4. Check current month for each user
print("\n4. TASKS BY MONTH (what calendar view sees):")
print("-" * 80)
current_date = timezone.now().date()
first_day = current_date.replace(day=1)
if current_date.month == 12:
    last_day = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
else:
    last_day = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)

print(f"Current month: {current_date.strftime('%B %Y')}")
print(f"Date range: {first_day} to {last_day}\n")

month_tasks = CalendarTask.objects.filter(scheduled_date__range=[first_day, last_day])
print(f"Tasks in current month: {month_tasks.count()}")
for task in month_tasks:
    print(f"  • {task.title} on {task.scheduled_date} → {task.assigned_to.display_name}")

# 5. Check for users and their tasks
print("\n5. TASKS PER USER:")
print("-" * 80)
for user in User.objects.filter(role='child'):
    user_tasks = CalendarTask.objects.filter(assigned_to=user, scheduled_date__range=[first_day, last_day])
    print(f"\n{user.display_name} ({user.username}):")
    print(f"  Total in database: {CalendarTask.objects.filter(assigned_to=user).count()}")
    print(f"  In current month: {user_tasks.count()}")
    for task in user_tasks:
        print(f"    • {task.title} on {task.scheduled_date}")

# 6. Check family filtering
print("\n6. FAMILY FILTERING:")
print("-" * 80)
for family in Family.objects.all():
    family_tasks = CalendarTask.objects.filter(family=family)
    print(f"\n{family.name}:")
    print(f"  Total tasks: {family_tasks.count()}")
    print(f"  In current month: {family_tasks.filter(scheduled_date__range=[first_day, last_day]).count()}")
    for task in family_tasks[:3]:
        print(f"    • {task.title} on {task.scheduled_date}")

# 7. Debug view logic for a specific user
print("\n7. VIEW LOGIC FOR PARENT USER:")
print("-" * 80)
parent = User.objects.filter(role='parent').first()
if parent:
    print(f"User: {parent.display_name}")
    print(f"Family: {parent.family}")

    tasks = CalendarTask.objects.filter(
        family=parent.family,
        scheduled_date__range=[first_day, last_day]
    )
    print(f"Tasks matching family+date filter: {tasks.count()}")

    for task in tasks:
        print(f"  • {task.title} on {task.scheduled_date}")

print("\n" + "="*80)
print("END DIAGNOSTIC")
print("="*80 + "\n")

