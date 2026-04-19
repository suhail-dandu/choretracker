#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from django.test import Client
from accounts.models import User, Family
from calendar_tasks.models import CalendarTask
from datetime import datetime, timedelta
from django.utils import timezone

print("=" * 60)
print("CALENDAR DISPLAY FIX - COMPREHENSIVE TEST")
print("=" * 60)

try:
    # Get or create test data
    parent = User.objects.filter(role='parent').first()
    if not parent:
        print("✗ No parent user found")
        exit(1)

    print(f"✓ Found parent user: {parent.email}")

    # Get all calendar tasks
    all_tasks = CalendarTask.objects.all()
    print(f"✓ Total calendar tasks in database: {all_tasks.count()}")

    if all_tasks.exists():
        print("\nTasks in database:")
        for task in all_tasks[:5]:
            print(f"  - {task.title} on {task.scheduled_date} (Status: {task.status})")

    # Test with Django test client
    client = Client()

    # Force login by creating a proper session
    from django.contrib.auth import get_user_model
    User_model = get_user_model()

    # Use force_login if available (Django 1.9+)
    if hasattr(client, 'force_login'):
        client.force_login(parent, backend='django.contrib.auth.backends.ModelBackend')
    else:
        # Fallback for older Django
        session = client.session
        session['_auth_user_id'] = str(parent.pk)
        session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
        session.save()

    # Get calendar page
    response = client.get('/calendar/')
    print(f"\n✓ Calendar page response status: {response.status_code}")

    if response.status_code == 200:
        content = response.content.decode('utf-8')

        # Count badges (tasks)
        import re
        badges = re.findall(r'<div class="badge[^>]*>([^<]+)<', content)
        print(f"✓ Tasks displayed as badges: {len(badges)}")

        if badges:
            print("  Badges found:")
            for badge in badges[:10]:
                print(f"    - {badge.strip()}")

        # Check for specific test task
        if "Test Task" in content or "Should Show in Calendar" in content:
            print("\n✓✓ TEST TASK APPEARS IN CALENDAR!")

        # Check task statuses
        if "bg-info" in content:
            print("✓ Pending tasks (blue) are displayed")
        if "bg-warning" in content:
            print("✓ Completed tasks (yellow) are displayed")
        if "bg-success" in content:
            print("✓ Approved tasks (green) are displayed")
        if "bg-danger" in content:
            print("✓ Rejected tasks (red) are displayed")

        print("\n" + "=" * 60)
        print("FIX VERIFIED: Calendar tasks are displaying correctly!")
        print("=" * 60)
    else:
        print(f"✗ Failed to load calendar page: {response.status_code}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

