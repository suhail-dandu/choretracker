#!/usr/bin/env python
"""
Generate ALL recurring tasks for current month and next months.
This ensures all recurring tasks are visible on the calendar.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from calendar_tasks.models import RecurringChoreTemplate, CalendarTask
from django.utils import timezone
from datetime import date, timedelta

print("\n" + "="*80)
print("GENERATE ALL RECURRING TASKS - IMMEDIATE GENERATION")
print("="*80)

today = timezone.now().date()
print(f"\nToday: {today}")

# Get all active recurring templates
templates = RecurringChoreTemplate.objects.filter(is_active=True)
print(f"Active recurring templates: {templates.count()}\n")

if templates.count() == 0:
    print("No recurring templates found!")
    exit(1)

# Generate for 60 days (current month + next 2 months)
start_date = today
end_date = today + timedelta(days=60)

print(f"Generating tasks from {start_date} to {end_date}\n")

total_created = 0

for template in templates:
    print(f"Processing: {template.chore_title} (assigned to {template.assigned_to.display_name})")
    print(f"  Frequency: {template.get_frequency_display()}")

    dates_to_create = []

    # Daily frequency
    if template.frequency == 'daily':
        current = start_date
        while current <= end_date:
            dates_to_create.append(current)
            current += timedelta(days=1)

    # Weekly frequency
    elif template.frequency == 'weekly':
        if template.days_of_week:
            target_days = [int(d.strip()) for d in template.days_of_week.split(',')]
        else:
            target_days = list(range(7))  # All days

        current = start_date
        while current <= end_date:
            if current.weekday() in target_days:
                dates_to_create.append(current)
            current += timedelta(days=1)

    # Monthly frequency
    elif template.frequency == 'monthly':
        day = template.day_of_month or start_date.day
        current = start_date
        while current <= end_date:
            try:
                target_date = current.replace(day=day)
                if target_date >= start_date and target_date <= end_date:
                    dates_to_create.append(target_date)
            except ValueError:
                pass

            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1)
            else:
                current = current.replace(month=current.month + 1, day=1)

    # Create tasks for each date
    created_count = 0
    for task_date in dates_to_create:
        # Check if task already exists
        existing = CalendarTask.objects.filter(
            recurring_template=template,
            scheduled_date=task_date,
            assigned_to=template.assigned_to
        ).exists()

        if not existing:
            try:
                task = CalendarTask.objects.create(
                    family=template.family,
                    assigned_to=template.assigned_to,
                    title=template.chore_title,
                    description=template.chore_description,
                    points=template.points,
                    category=template.category,
                    scheduled_date=task_date,
                    scheduled_time=template.scheduled_time,
                    recurring_template=template,
                    created_by=template.created_by,
                    status=CalendarTask.STATUS_PENDING
                )
                created_count += 1
                print(f"    ✓ Created: {template.chore_title} on {task_date}")
            except Exception as e:
                print(f"    ✗ Error creating task for {task_date}: {e}")

    print(f"  Created {created_count} new tasks\n")
    total_created += created_count

print("="*80)
print(f"✅ TOTAL CREATED: {total_created} tasks")
print("="*80 + "\n")

# Verify
print("VERIFICATION - Tasks now in database:")
all_tasks = CalendarTask.objects.all()
print(f"Total calendar tasks: {all_tasks.count()}\n")

# Show tasks for today and next 14 days
print("Tasks for next 14 days:")
for i in range(15):
    check_date = today + timedelta(days=i)
    tasks_on_date = CalendarTask.objects.filter(scheduled_date=check_date)
    if tasks_on_date.count() > 0:
        print(f"\n{check_date.strftime('%A, %B %d, %Y')}:")
        for task in tasks_on_date:
            print(f"  • {task.title} ({task.points} pts) → {task.assigned_to.display_name}")

