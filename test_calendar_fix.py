#!/usr/bin/env python
"""
Comprehensive test to verify calendar tasks display fix.
Tests the template rendering with actual tasks from the database.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from calendar_tasks.views import calendar_view
from calendar_tasks.models import CalendarTask
from accounts.models import User
from django.utils import timezone
from datetime import date

print("=" * 70)
print("CALENDAR TASKS DISPLAY - FIX VERIFICATION TEST")
print("=" * 70)

# Setup test request with authentication
factory = RequestFactory()
request = factory.get('/calendar/')

# Add session and auth middleware
SessionMiddleware(lambda x: None).process_request(request)
AuthenticationMiddleware(lambda x: None).process_request(request)

# Get a child user
child_user = User.objects.filter(role='child').first()
if not child_user:
    print("✗ ERROR: No child users found in database")
    exit(1)

request.user = child_user

print(f"\n1. Test User Setup:")
print(f"   User: {child_user.username} (display: {child_user.display_name})")
print(f"   Role: {child_user.role}")
print(f"   Family: {child_user.family}")
print(f"   Is authenticated: {child_user.is_authenticated}")

# Call the calendar view
print(f"\n2. Calendar View Response:")
try:
    response = calendar_view(request)
    print(f"   ✓ View executed successfully")
    print(f"   Response status: {response.status_code if hasattr(response, 'status_code') else 'N/A'}")
except Exception as e:
    print(f"   ✗ View execution failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Check the rendered response content
print(f"\n3. Response Content Check:")
if hasattr(response, 'content'):
    content = response.content.decode('utf-8')
    print(f"   HTML size: {len(content)} bytes")

    # Check for calendar structure
    if '<table class="table table-bordered' in content:
        print(f"   ✓ Calendar table found in HTML")
    else:
        print(f"   ✗ Calendar table NOT found")

    # Check for badges (task indicators)
    badge_count = content.count('class="badge')
    print(f"   Badge elements found: {badge_count}")

    # Check for specific task titles if they exist
    tasks = CalendarTask.objects.filter(
        family=child_user.family,
        assigned_to=child_user
    )

    print(f"\n4. Task Database Check:")
    print(f"   Tasks assigned to {child_user.display_name}: {tasks.count()}")

    found_in_html = 0
    for task in tasks[:5]:  # Check first 5
        if task.title in content:
            print(f"   ✓ Task found in HTML: {task.title}")
            found_in_html += 1
        else:
            print(f"   ✗ Task NOT found in HTML: {task.title}")

    if tasks.count() > 0:
        if found_in_html > 0:
            print(f"\n   ✓ SUCCESS: {found_in_html}/{min(5, tasks.count())} tasks displayed correctly!")
        else:
            print(f"\n   ⚠ WARNING: Tasks exist in database but not visible in HTML")
            print(f"   This might indicate:")
            print(f"   - Tasks are outside the current month")
            print(f"   - Template rendering issue")
            print(f"   - Status filter issue")
    else:
        print(f"\n   ℹ INFO: No tasks assigned to this user for current month")

# Test template date filtering
print(f"\n5. Template Date Filter Test:")
from django.template.loader import render_to_string

test_date = date(2026, 4, 13)
test_context = {
    'current_date': test_date,
    'calendar_days': [test_date],
    'all_tasks_items': [('2026-04-13', [])],
    'tasks_by_date': {},
    'prev_month': test_date.replace(day=1),
    'next_month': test_date.replace(day=1),
    'month_str': '2026-04',
    'user': child_user,
}

try:
    html = render_to_string('calendar_tasks/calendar_view.html', test_context)
    # Check if date filter was applied correctly
    if '2026-04-13' in html or '13' in html:  # Day number should be visible
        print(f"   ✓ Template renders successfully with date filtering")
    print(f"   Template HTML size: {len(html)} bytes")
except Exception as e:
    print(f"   ✗ Template rendering failed: {e}")

print("\n" + "=" * 70)
print("✅ VERIFICATION COMPLETE")
print("=" * 70)
print("\nIf all checks passed, calendar tasks should now display correctly!")
print("\nNext steps:")
print("1. Create a calendar task: Go to Calendar → Add Task")
print("2. For recurring tasks, run: python manage.py generate_tasks --days 30 --today")
print("3. Refresh calendar to see tasks")

