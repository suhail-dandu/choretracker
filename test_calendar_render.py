#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from calendar_tasks.models import CalendarTask
from accounts.models import User
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from calendar_tasks.views import calendar_view
from django.template import loader

# Create a test request
factory = RequestFactory()
request = factory.get('/calendar/')

# Authenticate as child user
user = User.objects.get(username='zaid_dandu')
request.user = user

print(f"User: {user.username}")
print(f"Is authenticated: {user.is_authenticated}")
print(f"Is child: {user.is_child}")
print(f"Family: {user.family}")
print()

# Call the view
response = calendar_view(request)

# If it's a render response, get the context
if hasattr(response, 'context_data'):
    context = response.context_data
    print("Context from response:")
    print(f"  - tasks_by_date: {context.get('tasks_by_date')}")
    print(f"  - all_tasks_items: {context.get('all_tasks_items')}")
    print(f"  - calendar_days (first 5): {context.get('calendar_days')[:5] if context.get('calendar_days') else None}")
elif hasattr(response, 'content'):
    print("Response has content, rendering...")
    content = response.content.decode('utf-8')
    # Try to find task titles in content
    if 'Test Task' in content:
        print("✓ Task title found in rendered HTML")
    else:
        print("✗ Task title NOT found in rendered HTML")

    # Check for any badges
    if 'badge' in content:
        print("✓ Badge elements found in HTML")
        # Count badges
        badge_count = content.count('badge')
        print(f"  Badge count: {badge_count}")
    else:
        print("✗ No badge elements found in HTML")

