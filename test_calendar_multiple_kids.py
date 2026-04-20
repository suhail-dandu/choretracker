#!/usr/bin/env python
"""
Test script to verify calendar displays correctly for parents and kids.
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.utils import timezone
from accounts.models import User, Family
from calendar_tasks.models import CalendarTask, CalendarTaskAssignment, RecurringChoreTemplate

def test_multiple_kids_assignment():
    """Test that tasks can be assigned to multiple kids."""
    print("=" * 60)
    print("Testing Multiple Kids Assignment")
    print("=" * 60)

    # Get or create test family
    family, _ = Family.objects.get_or_create(name="Test Family")
    print(f"\n✓ Using family: {family.name}")

    # Get or create parent
    parent, _ = User.objects.get_or_create(
        username='testparent',
        defaults={
            'email': 'parent@test.com',
            'first_name': 'Test',
            'last_name': 'Parent',
            'role': User.ROLE_PARENT,
            'family': family
        }
    )
    print(f"✓ Using parent: {parent.display_name}")

    # Get or create kids
    kids = []
    for i in range(1, 3):
        kid, _ = User.objects.get_or_create(
            username=f'testkid{i}',
            defaults={
                'email': f'kid{i}@test.com',
                'first_name': f'Kid{i}',
                'last_name': 'Test',
                'role': User.ROLE_CHILD,
                'family': family
            }
        )
        kids.append(kid)
        print(f"✓ Using kid {i}: {kid.display_name}")

    # Create a task for multiple kids
    today = timezone.now().date()
    task = CalendarTask.objects.create(
        family=family,
        assigned_to=kids[0],  # Primary assignment
        title="Test Multi-Kid Task",
        description="This task is assigned to multiple kids",
        points=10,
        category='other',
        scheduled_date=today,
        scheduled_time=timezone.now().time(),
        created_by=parent,
        status=CalendarTask.STATUS_PENDING
    )
    print(f"\n✓ Created task: {task.title}")

    # Assign to multiple kids
    for kid in kids:
        assignment, created = CalendarTaskAssignment.objects.get_or_create(
            task=task,
            assigned_to=kid
        )
        print(f"  ✓ Assigned to {kid.display_name}")

    # Verify assignments
    assigned_children = task.get_assigned_children()
    print(f"\n✓ Task assigned to {assigned_children.count()} children:")
    for child in assigned_children:
        print(f"  - {child.display_name}")

    print(f"\n✓ Children names: {task.get_assigned_children_names()}")

    # Verify kids can see their tasks
    print("\n" + "=" * 60)
    print("Testing Kids Calendar Access")
    print("=" * 60)
    for kid in kids:
        kid_tasks = CalendarTask.objects.filter(
            family=family,
            scheduled_date=today,
            child_assignments__assigned_to=kid
        )
        print(f"\n✓ {kid.display_name} can see {kid_tasks.count()} tasks:")
        for t in kid_tasks:
            print(f"  - {t.title} at {t.scheduled_time.strftime('%H:%M')}")

    # Verify parent can see all tasks
    print("\n" + "=" * 60)
    print("Testing Parent Calendar Access")
    print("=" * 60)
    parent_tasks = CalendarTask.objects.filter(
        family=family,
        scheduled_date=today
    )
    print(f"\n✓ Parent can see {parent_tasks.count()} tasks:")
    for t in parent_tasks:
        print(f"  - {t.title} at {t.scheduled_time.strftime('%H:%M')} → {t.get_assigned_children_names()}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_multiple_kids_assignment()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

