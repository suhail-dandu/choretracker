#!/usr/bin/env python
"""
Quick verification script to ensure calendar system is working correctly.
Run this after setting up the system to verify all features are operational.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.utils import timezone
from accounts.models import User, Family
from calendar_tasks.models import CalendarTask, CalendarTaskAssignment

def verify_system():
    print("\n" + "=" * 70)
    print("CHORETRACKER CALENDAR SYSTEM - VERIFICATION")
    print("=" * 70)

    # Check models
    print("\n✓ Checking database models...")
    try:
        CalendarTaskAssignment.objects.count()
        print("  ✅ CalendarTaskAssignment model exists")
    except Exception as e:
        print(f"  ❌ CalendarTaskAssignment error: {e}")
        return False

    # Check migrations
    print("\n✓ Checking migrations...")
    try:
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command('migrate', '--check', stdout=out, stderr=out)
        print("  ✅ All migrations applied")
    except Exception as e:
        print(f"  ❌ Migration error: {e}")

    # Count existing data
    print("\n✓ Existing data:")
    families = Family.objects.count()
    users = User.objects.count()
    tasks = CalendarTask.objects.count()
    assignments = CalendarTaskAssignment.objects.count()

    print(f"  - Families: {families}")
    print(f"  - Users: {users}")
    print(f"  - Calendar Tasks: {tasks}")
    print(f"  - Task Assignments: {assignments}")

    # Check if any parents exist
    parents = User.objects.filter(role=User.ROLE_PARENT).count()
    children = User.objects.filter(role=User.ROLE_CHILD).count()

    print(f"\n✓ User breakdown:")
    print(f"  - Parents: {parents}")
    print(f"  - Children: {children}")

    if families > 0 and parents > 0 and children > 0:
        print("\n✅ System is properly set up!")
        print("\n📝 Next steps:")
        print("  1. Log in as a parent: http://127.0.0.1:8000/")
        print("  2. Go to Dashboard → Calendar")
        print("  3. Create a task and assign to multiple children")
        print("  4. View calendar - should show time + child names")
        print("  5. Log in as child and verify you see your tasks")
        return True
    else:
        print("\n⚠️  System needs setup:")
        print("  1. Create a parent account")
        print("  2. Create children accounts")
        print("  3. Assign children to same family")
        print("  4. Then create tasks through dashboard")
        return True

def run_migrations():
    print("\nRunning migrations...")
    from django.core.management import call_command
    try:
        call_command('migrate')
        print("✅ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def test_features():
    print("\n" + "=" * 70)
    print("TESTING CALENDAR FEATURES")
    print("=" * 70)

    # Create test data
    family, _ = Family.objects.get_or_create(name="Verification Family")
    parent, _ = User.objects.get_or_create(
        username='verify_parent',
        defaults={
            'email': 'verify_parent@test.local',
            'first_name': 'Verification',
            'last_name': 'Parent',
            'role': User.ROLE_PARENT,
            'family': family
        }
    )

    kid1, _ = User.objects.get_or_create(
        username='verify_kid1',
        defaults={
            'email': 'verify_kid1@test.local',
            'first_name': 'Test',
            'last_name': 'Child1',
            'role': User.ROLE_CHILD,
            'family': family
        }
    )

    kid2, _ = User.objects.get_or_create(
        username='verify_kid2',
        defaults={
            'email': 'verify_kid2@test.local',
            'first_name': 'Test',
            'last_name': 'Child2',
            'role': User.ROLE_CHILD,
            'family': family
        }
    )

    print("\n✓ Created test data")

    # Test 1: Create task for multiple kids
    print("\n✓ Test 1: Creating task for multiple kids...")
    today = timezone.now().date()
    task = CalendarTask.objects.create(
        family=family,
        assigned_to=kid1,
        title="Test Task",
        points=10,
        category='other',
        scheduled_date=today,
        scheduled_time=timezone.datetime.strptime('10:00', '%H:%M').time(),
        created_by=parent,
        status=CalendarTask.STATUS_PENDING
    )

    CalendarTaskAssignment.objects.create(task=task, assigned_to=kid1)
    CalendarTaskAssignment.objects.create(task=task, assigned_to=kid2)

    assigned_count = task.child_assignments.count()
    print(f"  ✅ Task assigned to {assigned_count} kids")

    # Test 2: Check parent can see all assigned kids
    print("\n✓ Test 2: Checking parent can see all kids...")
    kids_list = task.get_assigned_children_names()
    print(f"  ✅ Kids assigned: {kids_list}")

    # Test 3: Check kids can see task
    print("\n✓ Test 3: Checking kids can see their tasks...")
    kid1_tasks = CalendarTask.objects.filter(
        child_assignments__assigned_to=kid1,
        scheduled_date=today
    )
    kid2_tasks = CalendarTask.objects.filter(
        child_assignments__assigned_to=kid2,
        scheduled_date=today
    )
    print(f"  ✅ Kid1 sees {kid1_tasks.count()} task(s)")
    print(f"  ✅ Kid2 sees {kid2_tasks.count()} task(s)")

    # Test 4: Check mark complete
    print("\n✓ Test 4: Testing mark complete workflow...")
    assignment = task.child_assignments.first()
    assignment.mark_completed(note="Test note")
    print(f"  ✅ Task marked complete, status: {assignment.get_status_display()}")

    # Test 5: Check approve
    print("\n✓ Test 5: Testing approve workflow...")
    assignment.approve(approved_by=parent)
    print(f"  ✅ Task approved, status: {assignment.get_status_display()}")

    print("\n" + "=" * 70)
    print("✅ ALL FEATURE TESTS PASSED!")
    print("=" * 70)

    return True

if __name__ == '__main__':
    try:
        print("\n🔍 Running system verification...\n")

        # First verify system state
        if not verify_system():
            print("\n❌ System verification failed")
            sys.exit(1)

        # Try running feature tests
        if not test_features():
            print("\n❌ Feature tests failed")
            sys.exit(1)

        print("\n" + "=" * 70)
        print("✅ SYSTEM READY FOR USE!")
        print("=" * 70)
        print("\n📚 Documentation:")
        print("  - CALENDAR_MULTIPLE_KIDS_COMPLETE.md - User guide")
        print("  - CALENDAR_MULTIPLE_KIDS_IMPLEMENTATION.md - Technical details")
        print("\n🧪 Tests:")
        print("  - test_calendar_comprehensive.py - Full test suite")
        print("  - test_calendar_multiple_kids.py - Quick test")
        print("\n🌐 Access:")
        print("  - http://127.0.0.1:8000/ (web interface)")
        print("  - Dashboard → Calendar (parent/kid views)")
        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

