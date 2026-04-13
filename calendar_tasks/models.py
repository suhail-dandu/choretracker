from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from datetime import datetime, timedelta, time
from accounts.models import User, Family


class RecurringChoreTemplate(models.Model):
    """Template for recurring chores that generate assignments automatically."""
    FREQUENCY_DAILY = 'daily'
    FREQUENCY_WEEKLY = 'weekly'
    FREQUENCY_MONTHLY = 'monthly'

    FREQUENCY_CHOICES = [
        (FREQUENCY_DAILY, 'Daily'),
        (FREQUENCY_WEEKLY, 'Weekly'),
        (FREQUENCY_MONTHLY, 'Monthly'),
    ]

    # Weekday choices (0=Monday, 6=Sunday)
    DAY_CHOICES = [
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ]

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='recurring_templates')
    chore_title = models.CharField(max_length=150, help_text="Title of the recurring chore")
    chore_description = models.TextField(blank=True)
    points = models.IntegerField(help_text="Points for completing this chore")
    category = models.CharField(max_length=20, choices=[
        ('cleaning', '🧹 Cleaning'),
        ('cooking', '🍳 Cooking'),
        ('garden', '🌱 Garden'),
        ('laundry', '👕 Laundry'),
        ('pets', '🐾 Pets'),
        ('homework', '📚 Homework'),
        ('shopping', '🛒 Shopping'),
        ('other', '⭐ Other'),
    ], default='other')

    # Recurrence settings
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default=FREQUENCY_WEEKLY)
    days_of_week = models.CharField(
        max_length=20, blank=True,
        help_text="Comma-separated day numbers (0=Mon, 6=Sun) for weekly recurrence. Leave blank for all days."
    )
    day_of_month = models.IntegerField(null=True, blank=True, help_text="Day of month for monthly recurrence")

    # Assignment settings
    assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='recurring_templates',
        limit_choices_to={'role': 'child'}
    )
    scheduled_time = models.TimeField(default='09:00', help_text="Time of day to schedule the chore")

    # Control
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True, help_text="Leave blank for no end date")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_recurring_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    last_generated = models.DateTimeField(null=True, blank=True, help_text="Last time tasks were auto-generated")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Recurring Chore Template'
        verbose_name_plural = 'Recurring Chore Templates'

    def __str__(self):
        return f"{self.chore_title} ({self.frequency}) → {self.assigned_to.display_name}"

    def get_next_due_date(self):
        """Calculate the next due date based on frequency."""
        today = timezone.now().date()
        scheduled_datetime = timezone.make_aware(
            datetime.combine(today, self.scheduled_time)
        )

        if self.frequency == self.FREQUENCY_DAILY:
            if scheduled_datetime <= timezone.now():
                return timezone.make_aware(
                    datetime.combine(today + timedelta(days=1), self.scheduled_time)
                )
            return scheduled_datetime

        elif self.frequency == self.FREQUENCY_WEEKLY:
            if self.days_of_week:
                target_days = [int(d.strip()) for d in self.days_of_week.split(',')]
            else:
                target_days = list(range(7))

            # Find next occurrence on target day
            current_day = today.weekday()
            for offset in range(1, 8):
                next_day = (current_day + offset) % 7
                if next_day in target_days:
                    next_date = today + timedelta(days=offset)
                    return timezone.make_aware(
                        datetime.combine(next_date, self.scheduled_time)
                    )
            return scheduled_datetime

        elif self.frequency == self.FREQUENCY_MONTHLY:
            day = self.day_of_month or today.day
            try:
                next_date = today.replace(day=day)
            except ValueError:
                # Handle day doesn't exist in month (e.g., Feb 30)
                next_date = today + timedelta(days=1)

            if next_date <= today:
                if next_date.month == 12:
                    next_date = next_date.replace(year=next_date.year + 1, month=1)
                else:
                    next_date = next_date.replace(month=next_date.month + 1)

            return timezone.make_aware(datetime.combine(next_date, self.scheduled_time))

        return scheduled_datetime


class SchedulePattern(models.Model):
    """Custom schedule pattern for holidays and special dates."""
    PATTERN_TYPE_HOLIDAY = 'holiday'
    PATTERN_TYPE_SPECIAL = 'special'
    PATTERN_TYPE_BREAK = 'break'

    PATTERN_TYPES = [
        (PATTERN_TYPE_HOLIDAY, 'Holiday (no chores)'),
        (PATTERN_TYPE_SPECIAL, 'Special Day (custom chores)'),
        (PATTERN_TYPE_BREAK, 'Break Period (no chores)'),
    ]

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='schedule_patterns')
    name = models.CharField(max_length=100, help_text="e.g., Christmas, Summer Break")
    pattern_type = models.CharField(max_length=20, choices=PATTERN_TYPES, default=PATTERN_TYPE_HOLIDAY)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"

    def is_active_today(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and self.is_active


class CalendarTask(models.Model):
    """Individual task on the calendar with time scheduling."""
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_SKIPPED = 'skipped'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed - Awaiting Approval'),
        (STATUS_APPROVED, 'Approved ✅'),
        (STATUS_REJECTED, 'Rejected ❌'),
        (STATUS_SKIPPED, 'Skipped'),
    ]

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='calendar_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_tasks')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    points = models.IntegerField(help_text="Points for completing this task")
    category = models.CharField(max_length=20, choices=[
        ('cleaning', '🧹 Cleaning'),
        ('cooking', '🍳 Cooking'),
        ('garden', '🌱 Garden'),
        ('laundry', '👕 Laundry'),
        ('pets', '🐾 Pets'),
        ('homework', '📚 Homework'),
        ('shopping', '🛒 Shopping'),
        ('other', '⭐ Other'),
    ], default='other')

    # Schedule
    scheduled_date = models.DateField(help_text="Date the task is scheduled for")
    scheduled_time = models.TimeField(help_text="Time the task should be completed")
    due_time = models.TimeField(null=True, blank=True, help_text="Deadline time")

    # Relationships
    recurring_template = models.ForeignKey(
        RecurringChoreTemplate, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='generated_tasks'
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_calendar_tasks')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_calendar_tasks')
    rejection_reason = models.CharField(max_length=200, blank=True)
    note = models.TextField(blank=True, help_text="Note from kid when marking as done")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date', 'scheduled_time']
        indexes = [
            models.Index(fields=['family', 'scheduled_date']),
            models.Index(fields=['assigned_to', 'scheduled_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.assigned_to.display_name} ({self.scheduled_date})"

    @property
    def is_overdue(self):
        if self.status == self.STATUS_PENDING:
            scheduled_datetime = timezone.make_aware(
                datetime.combine(self.scheduled_date, self.due_time or self.scheduled_time)
            )
            return scheduled_datetime < timezone.now()
        return False

    def mark_completed(self, note=''):
        """Mark task as completed."""
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.note = note
        self.save(update_fields=['status', 'completed_at', 'note', 'updated_at'])

    def approve(self, approved_by):
        """Approve the task and award points."""
        self.status = self.STATUS_APPROVED
        self.approved_at = timezone.now()
        self.approved_by = approved_by
        self.save(update_fields=['status', 'approved_at', 'approved_by', 'updated_at'])

        # Award points to the child
        self.assigned_to.add_points(
            self.points,
            reason=f"Calendar task completed: {self.title}",
            added_by=approved_by
        )

    def reject(self, approved_by, reason=''):
        """Reject the task."""
        self.status = self.STATUS_REJECTED
        self.approved_by = approved_by
        self.rejection_reason = reason
        self.save(update_fields=['status', 'approved_by', 'rejection_reason', 'updated_at'])


class BadDeed(models.Model):
    """Negative behavior tracking - parents directly deduct points."""
    CATEGORY_CHOICES = [
        ('behavior', '😠 Bad Behavior'),
        ('attitude', '😤 Bad Attitude'),
        ('disrespect', '🤨 Disrespect'),
        ('disobedience', '⛔ Disobedience'),
        ('lying', '🤥 Lying'),
        ('fighting', '👊 Fighting'),
        ('laziness', '😴 Laziness'),
        ('other', '⚠️ Other'),
    ]

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='bad_deeds')
    title = models.CharField(max_length=150, help_text="Name of the bad deed")
    description = models.TextField(blank=True)
    negative_points = models.IntegerField(
        help_text="Points to deduct (enter positive number, will be negated)"
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    is_recurring = models.BooleanField(default=False)

    # Recurrence settings (same as RecurringChoreTemplate)
    frequency = models.CharField(
        max_length=10,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
        default='weekly',
        blank=True
    )
    days_of_week = models.CharField(
        max_length=20, blank=True,
        help_text="Comma-separated day numbers (0=Mon, 6=Sun) for weekly recurrence"
    )
    day_of_month = models.IntegerField(null=True, blank=True, help_text="Day of month for monthly")
    scheduled_time = models.TimeField(default='09:00', help_text="Time of day for calendar")

    assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='bad_deeds_assigned',
        limit_choices_to={'role': 'child'},
        help_text="Child assigned to this bad deed"
    )

    is_active = models.BooleanField(default=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_bad_deeds')
    created_at = models.DateTimeField(auto_now_add=True)
    last_applied = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (-{self.negative_points} pts)"

    @property
    def actual_points(self):
        """Return negative points."""
        return -abs(self.negative_points)


class BadDeedInstance(models.Model):
    """Individual bad deed instance - direct point deduction."""
    STATUS_ACTIVE = 'active'
    STATUS_REMOVED = 'removed'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active (Points Deducted)'),
        (STATUS_REMOVED, 'Removed (Points Restored)'),
    ]

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='bad_deed_instances')
    bad_deed = models.ForeignKey(BadDeed, on_delete=models.CASCADE, related_name='instances', null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bad_deed_instances')

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    negative_points = models.IntegerField()
    category = models.CharField(max_length=20, choices=BadDeed.CATEGORY_CHOICES, default='other')

    reason = models.TextField(help_text="Reason for deduction")
    created_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_bad_deed_instances')
    removed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='removed_bad_deeds')
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.assigned_to.display_name}: {self.negative_points} pts)"
