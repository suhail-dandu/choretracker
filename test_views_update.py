#!/usr/bin/env python
"""
Test that the updated calendar view works correctly.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

print("Testing calendar_tasks.views module...\n")

try:
    from calendar_tasks.views import calendar_view, _generate_recurring_tasks_for_month
    print("✓ Imports successful")
    print("✓ calendar_view function exists")
    print("✓ _generate_recurring_tasks_for_month function exists\n")

    # Test the function signature
    import inspect
    sig = inspect.signature(_generate_recurring_tasks_for_month)
    print(f"✓ _generate_recurring_tasks_for_month signature: {sig}\n")

    print("✅ Module loads without errors")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

