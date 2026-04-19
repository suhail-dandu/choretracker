#!/usr/bin/env python
"""
Complete debugging tool to understand why tasks aren't showing.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from calendar_tasks.models import CalendarTask, RecurringChoreTemplate, BadDeed, BadDeedInstance
from accounts.models import User, Family
from django.utils import timezone
from datetime import date, timedelta
import calendar as cal_module

print("\n" + "█"*80)
print("█ COMPREHENSIVE CALENDAR DEBUGGING TOOL")
print("█"*80 + "\n")

# Current date info
today = timezone.now().date()
current_month_start = today.replace(day=1)
if today.month == 12:
    current_month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
else:
    current_month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

print(f"Today: {today} ({today.strftime('%A')})")
print(f"Current Month: {today.strftime('%B %Y')}")
print(f"Month Range: {current_month_start} to {current_month_end}")

# SECTION 1: Database Content
print(f"\n{'='*80}")
print("SECTION 1: DATABASE CONTENT")
print(f"{'='*80}\n")

print("📊 CALENDAR TASKS:")
all_tasks = CalendarTask.objects.all().order_by('scheduled_date')
print(f"  Total in database: {all_tasks.count()}")
if all_tasks.count() > 0:
    print(f"  Date range: {all_tasks.first().scheduled_date} to {all_tasks.last().scheduled_date}")
    print(f"  By status:")
    for status, label in CalendarTask.STATUS_CHOICES:
        count = all_tasks.filter(status=status).count()
        print(f"    - {label}: {count}")

print(f"\n🔄 RECURRING TEMPLATES:")
templates = RecurringChoreTemplate.objects.all()
print(f"  Total: {templates.count()}")
print(f"  Active: {templates.filter(is_active=True).count()}")
for t in templates:
    print(f"    • {t.chore_title} ({t.get_frequency_display()}) → {t.assigned_to.display_name}")

print(f"\n⚠️  BAD DEEDS:")
bad_deeds = BadDeed.objects.all()
print(f"  Total: {bad_deeds.count()}")
print(f"  Recurring: {bad_deeds.filter(is_recurring=True).count()}")

# SECTION 2: Current Month Tasks
print(f"\n{'='*80}")
print("SECTION 2: CURRENT MONTH TASKS")
print(f"{'='*80}\n")

month_tasks = CalendarTask.objects.filter(
    scheduled_date__range=[current_month_start, current_month_end]
).order_by('scheduled_date')

print(f"Tasks in {today.strftime('%B %Y')}: {month_tasks.count()}\n")

if month_tasks.count() > 0:
    current_print = current_month_start
    while current_print <= current_month_end:
        tasks_today = month_tasks.filter(scheduled_date=current_print)
        if tasks_today.count() > 0:
            print(f"{current_print.strftime('%a, %b %d')}:")
            for task in tasks_today:
                print(f"  • {task.title} ({task.points} pts) → {task.assigned_to.display_name}")
        current_print += timedelta(days=1)
else:
    print("⚠️  NO TASKS IN CURRENT MONTH!")

# SECTION 3: User-Specific View
print(f"\n{'='*80}")
print("SECTION 3: USER-SPECIFIC CALENDAR VIEW")
print(f"{'='*80}\n")

for user in User.objects.filter(family__isnull=False):
    print(f"\n👤 {user.display_name} ({user.role}) - Family: {user.family}")

    # What the view sees
    if user.role == 'parent':
        tasks_seen = CalendarTask.objects.filter(
            family=user.family,
            scheduled_date__range=[current_month_start, current_month_end]
        )
    else:  # child
        tasks_seen = CalendarTask.objects.filter(
            family=user.family,
            assigned_to=user,
            scheduled_date__range=[current_month_start, current_month_end]
        )

    print(f"  Tasks visible in calendar: {tasks_seen.count()}")

    if tasks_seen.count() > 0:
        for task in tasks_seen[:5]:
            print(f"    • {task.title} on {task.scheduled_date}")

# SECTION 4: Debug View Logic
print(f"\n{'='*80}")
print("SECTION 4: TEMPLATE RENDERING TEST")
print(f"{'='*80}\n")

# Simulate calendar day comparison
print("Testing date matching logic (THE FIX):\n")

sample_dates = ['2026-04-13', '2026-04-19', '2026-04-20']

for date_str in sample_dates:
    y, m, d = date_str.split('-')
    day_obj = date(int(y), int(m), int(d))

    # Old way (broken)
    old_result = date_str == day_obj.isoformat()

    # New way (fixed)
    formatted = day_obj.strftime('%Y-%m-%d')
    new_result = date_str == formatted

    print(f"Date: {date_str}")
    print(f"  Old (broken):    '{date_str}' == day.isoformat()      → {old_result}")
    print(f"  New (fixed):     '{date_str}' == day|date:'Y-m-d'   → {new_result}")
    print()

# SECTION 5: Diagnostic Recommendations
print(f"\n{'='*80}")
print("SECTION 5: DIAGNOSTIC RECOMMENDATIONS")
print(f"{'='*80}\n")

issues = []

# Check 1: Are there any tasks?
if all_tasks.count() == 0:
    issues.append("❌ NO TASKS IN DATABASE - Create tasks or generate recurring tasks")
else:
    print(f"✓ Tasks exist: {all_tasks.count()} total")

# Check 2: Are there tasks in current month?
if month_tasks.count() == 0:
    issues.append("❌ NO TASKS IN CURRENT MONTH - Tasks may be in past/future months")
else:
    print(f"✓ Current month has tasks: {month_tasks.count()}")

# Check 3: Are there active templates?
active_templates = templates.filter(is_active=True)
if active_templates.count() > 0 and CalendarTask.objects.filter(recurring_template__isnull=False).count() == 0:
    issues.append("⚠️  TEMPLATES EXIST BUT NO GENERATED TASKS - Run: python generate_all_tasks.py")
else:
    print(f"✓ Recurring tasks exist or no templates")

# Check 4: Family filtering
for family in Family.objects.all():
    tasks = CalendarTask.objects.filter(family=family)
    if family.members.count() == 0:
        issues.append(f"⚠️  Family '{family.name}' has no members")
    elif tasks.count() == 0:
        issues.append(f"⚠️  Family '{family.name}' has no tasks")

if not issues:
    print("✓ Database structure looks good")
else:
    print("\n⚠️  ISSUES FOUND:")
    for issue in issues:
        print(f"  {issue}")

# SECTION 6: Quick Fixes
print(f"\n{'='*80}")
print("SECTION 6: QUICK FIXES")
print(f"{'='*80}\n")

print("Run these commands to generate tasks:\n")
print("  Option 1: Generate all recurring tasks NOW")
print("  $ python generate_all_tasks.py\n")
print("  Option 2: Use Django management command")
print("  $ python manage.py generate_tasks --today --days 60\n")

print("Then verify:")
print("  $ python deep_diagnostic.py")
print("  $ python verify_calendar_fix.py\n")

print(f"{'='*80}\n")

