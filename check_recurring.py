#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from calendar_tasks.models import CalendarTask, RecurringChoreTemplate, BadDeed, BadDeedInstance
from datetime import datetime, timedelta
from accounts.models import User
from django.utils import timezone

# Check if there are any recurring templates
templates = RecurringChoreTemplate.objects.all()
print(f"Recurring templates: {templates.count()}")
for t in templates:
    print(f"  - {t.chore_title} → {t.assigned_to.display_name} ({t.frequency})")

# Check bad deeds
bad_deeds = BadDeed.objects.all()
print(f"\nBad deeds: {bad_deeds.count()}")
for bd in bad_deeds:
    print(f"  - {bd.title} → {bd.assigned_to.display_name} ({-bd.negative_points} pts)")

# Check bad deed instances
bad_deed_instances = BadDeedInstance.objects.all()
print(f"\nBad deed instances: {bad_deed_instances.count()}")
for bdi in bad_deed_instances:
    print(f"  - {bdi.title} → {bdi.assigned_to.display_name} ({bdi.negative_points} pts)")

