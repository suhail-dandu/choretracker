from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from calendar_tasks.models import RecurringChoreTemplate, CalendarTask, BadDeed, BadDeedInstance
from django.db import models


class Command(BaseCommand):
    help = 'Generate calendar tasks from recurring templates and bad deeds'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to generate tasks for (default: 30)',
        )
        parser.add_argument(
            '--today',
            action='store_true',
            help='Generate tasks for today as well',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        days_ahead = options['days']
        include_today = options['today']

        # If include_today, start from today, else start from tomorrow
        start_date = today if include_today else today + timedelta(days=1)
        end_date = today + timedelta(days=days_ahead)

        self.stdout.write(
            self.style.SUCCESS(
                f'Generating tasks from {start_date} to {end_date}'
            )
        )

        # ========== Generate Recurring Chore Tasks ==========
        templates = RecurringChoreTemplate.objects.filter(
            is_active=True,
            start_date__lte=end_date
        )

        # Filter by end_date if set
        templates = templates.filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=start_date)
        )

        chore_count = 0
        for template in templates:
            # Determine which dates should have tasks
            dates_to_create = []

            if template.frequency == 'daily':
                dates_to_create = [
                    start_date + timedelta(days=i)
                    for i in range((end_date - start_date).days + 1)
                ]

            elif template.frequency == 'weekly':
                if template.days_of_week:
                    target_days = [int(d.strip()) for d in template.days_of_week.split(',')]
                else:
                    target_days = list(range(7))  # All days

                current = start_date
                while current <= end_date:
                    if current.weekday() in target_days:
                        dates_to_create.append(current)
                    current += timedelta(days=1)

            elif template.frequency == 'monthly':
                day = template.day_of_month or start_date.day
                current = start_date
                while current <= end_date:
                    try:
                        target_date = current.replace(day=day)
                        if target_date >= start_date and target_date <= end_date:
                            dates_to_create.append(target_date)
                    except ValueError:
                        pass  # Day doesn't exist in this month

                    # Move to next month
                    if current.month == 12:
                        current = current.replace(year=current.year + 1, month=1, day=1)
                    else:
                        current = current.replace(month=current.month + 1, day=1)

            # Create tasks for each date
            for date_to_create in dates_to_create:
                # Check if task already exists
                existing = CalendarTask.objects.filter(
                    recurring_template=template,
                    scheduled_date=date_to_create,
                    assigned_to=template.assigned_to
                ).exists()

                if not existing:
                    CalendarTask.objects.create(
                        family=template.family,
                        assigned_to=template.assigned_to,
                        title=template.chore_title,
                        description=template.chore_description,
                        points=template.points,
                        category=template.category,
                        scheduled_date=date_to_create,
                        scheduled_time=template.scheduled_time,
                        recurring_template=template,
                        created_by=template.created_by,
                    )
                    chore_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Created {chore_count} recurring chore tasks')
        )

        # ========== Generate Bad Deed Tasks ==========
        bad_deeds = BadDeed.objects.filter(
            is_active=True,
            is_recurring=True,
            start_date__lte=end_date
        )

        bad_deeds = bad_deeds.filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=start_date)
        )

        bad_deed_count = 0
        for bad_deed in bad_deeds:
            # Determine which dates should have bad deeds
            dates_to_create = []

            if bad_deed.frequency == 'daily':
                dates_to_create = [
                    start_date + timedelta(days=i)
                    for i in range((end_date - start_date).days + 1)
                ]

            elif bad_deed.frequency == 'weekly':
                if bad_deed.days_of_week:
                    target_days = [int(d.strip()) for d in bad_deed.days_of_week.split(',')]
                else:
                    target_days = list(range(7))

                current = start_date
                while current <= end_date:
                    if current.weekday() in target_days:
                        dates_to_create.append(current)
                    current += timedelta(days=1)

            elif bad_deed.frequency == 'monthly':
                day = bad_deed.day_of_month or start_date.day
                current = start_date
                while current <= end_date:
                    try:
                        target_date = current.replace(day=day)
                        if target_date >= start_date and target_date <= end_date:
                            dates_to_create.append(target_date)
                    except ValueError:
                        pass

                    if current.month == 12:
                        current = current.replace(year=current.year + 1, month=1, day=1)
                    else:
                        current = current.replace(month=current.month + 1, day=1)

            # Create calendar entries for bad deeds
            for date_to_create in dates_to_create:
                # Create a calendar task entry to show in calendar
                existing = CalendarTask.objects.filter(
                    family=bad_deed.family,
                    assigned_to=bad_deed.assigned_to,
                    title=bad_deed.title,
                    scheduled_date=date_to_create,
                    category='other'
                ).exists()

                if not existing:
                    CalendarTask.objects.create(
                        family=bad_deed.family,
                        assigned_to=bad_deed.assigned_to,
                        title=f"⚠️ {bad_deed.title}",
                        description=bad_deed.description,
                        points=-abs(bad_deed.negative_points),
                        category=bad_deed.category,
                        scheduled_date=date_to_create,
                        scheduled_time=bad_deed.scheduled_time,
                        status='pending',  # Mark as pending so it shows in calendar
                        created_by=bad_deed.created_by,
                    )
                    bad_deed_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Created {bad_deed_count} bad deed calendar entries')
        )

        total = chore_count + bad_deed_count
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Successfully generated {total} total tasks!')
        )

