#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from calendar_tasks.models import CalendarTask
from accounts.models import User, Family
from django.utils import timezone
from datetime import date

# Get parent user
parent = User.objects.filter(is_parent=True).first()
if not parent:
    print("No parent user found!")
    exit()

print(f"Parent: {parent.username}, Family: {parent.family}")

# Create a new test task manually
print("\nCreating a new test task...")

task = CalendarTask.objects.create(
    family=parent.family,
    assigned_to=parent.family.children.first(),
    title="Manual Test Task",
    description="This is a manual test task",
    points=50,
    category='cleaning',
    scheduled_date=date(2026, 4, 19),  # Today
    scheduled_time=timezone.now().time(),
    created_by=parent,
    status=CalendarTask.STATUS_PENDING
)

print(f"Created task: {task}")
print(f"  ID: {task.id}")
print(f"  Family: {task.family}")
print(f"  Assigned to: {task.assigned_to}")
print(f"  Date: {task.scheduled_date}")

# Now try to retrieve it
print("\nRetrieving the task...")
retrieved = CalendarTask.objects.get(pk=task.id)
print(f"Retrieved task: {retrieved}")
print(f"  Title: {retrieved.title}")
print(f"  Family: {retrieved.family}")

# Delete it
task.delete()
print("\nTask deleted")

