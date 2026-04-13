from celery import shared_task
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
from .models import RecurringChoreTemplate, CalendarTask
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def generate_recurring_tasks():
    """Generate tasks for active recurring templates (run daily)."""
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    # Get all active recurring templates
    templates = RecurringChoreTemplate.objects.filter(
        is_active=True,
        start_date__lte=today
    )

    # Filter by end_date if set
    templates = templates.filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
    )

    count = 0
    for template in templates:
        # Check if we should generate a task
        next_due = template.get_next_due_date()
        next_due_date = next_due.date()

        # Only generate if tomorrow is the next scheduled date
        if next_due_date == tomorrow:
            # Check for existing task to avoid duplicates
            existing = CalendarTask.objects.filter(
                recurring_template=template,
                scheduled_date=next_due_date,
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
                    scheduled_date=next_due_date,
                    scheduled_time=template.scheduled_time,
                    recurring_template=template,
                    created_by=template.created_by,
                )
                count += 1

    return f"Generated {count} recurring tasks"


@shared_task
def send_approval_notification(calendar_task_id):
    """Send email to parents when child completes a calendar task."""
    from .models import CalendarTask

    try:
        task = CalendarTask.objects.get(id=calendar_task_id)
        parents = task.family.members.filter(role='parent')

        subject = f"📋 {task.assigned_to.display_name} completed: {task.title}"
        message = f"""
        Hello,
        
        {task.assigned_to.display_name} has completed the calendar task "{task.title}" on {task.scheduled_date}.
        
        Task Details:
        - Title: {task.title}
        - Date: {task.scheduled_date}
        - Time: {task.scheduled_time}
        - Points: {task.points}
        {f'- Note: {task.note}' if task.note else ''}
        
        Please review and approve or reject this task in your dashboard.
        
        Best regards,
        ChoreTracker Team
        """

        recipient_list = [parent.email for parent in parents if parent.email]

        if recipient_list:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                fail_silently=True,
            )
    except Exception as e:
        print(f"Error sending notification: {e}")


@shared_task
def send_password_reset_email(user_id, reset_link):
    """Send password reset email."""
    from accounts.models import User

    try:
        user = User.objects.get(id=user_id)

        subject = "🔐 Reset your ChoreTracker password"
        message = f"""
        Hello {user.first_name or user.username},
        
        We received a request to reset your password. Click the link below to reset it:
        
        {reset_link}
        
        If you didn't request this, you can ignore this email.
        
        This link expires in 24 hours.
        
        Best regards,
        ChoreTracker Team
        """

        if user.email:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
    except Exception as e:
        print(f"Error sending password reset email: {e}")


