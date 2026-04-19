#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from calendar_tasks.models import CalendarTask
from accounts.models import User

# Get all tasks
all_tasks = CalendarTask.objects.all()
print(f"All tasks in database: {all_tasks.count()}")
for task in all_tasks:
    print(f"  Task: {task.title}")
    print(f"    - Family: {task.family}")
    print(f"    - Assigned to: {task.assigned_to} (role: {task.assigned_to.role})")
    print(f"    - Created by: {task.created_by}")
    print()

# Get parents and children
print("Users:")
for user in User.objects.all():
    print(f"  {user.username}: role={user.role}, family={user.family}, is_parent={user.is_parent}, is_child={user.is_child}")

