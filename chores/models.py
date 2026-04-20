from django.db import models
from django.utils import timezone
from accounts.models import User, Family


class Chore(models.Model):
    """A chore template defined by a parent."""
    CATEGORY_CHOICES = [
        ('cleaning', '🧹 Cleaning'),
        ('cooking', '🍳 Cooking'),
        ('garden', '🌱 Garden'),
        ('laundry', '👕 Laundry'),
        ('pets', '🐾 Pets'),
        ('homework', '📚 Homework'),
        ('shopping', '🛒 Shopping'),
        ('other', '⭐ Other'),
    ]

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='chores')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    points = models.IntegerField(help_text="Positive = reward, negative = penalty")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    icon = models.CharField(max_length=10, default='⭐')
    is_recurring = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_chores')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.points >= 0 else ''
        return f"{self.title} ({sign}{self.points} pts)"

    @property
    def is_penalty(self):
        return self.points < 0

    @property
    def points_display(self):
        if self.points >= 0:
            return f"+{self.points}"
        return str(self.points)

    @property
    def category_icon(self):
        icons = {
            'cleaning': '🧹', 'cooking': '🍳', 'garden': '🌱',
            'laundry': '👕', 'pets': '🐾', 'homework': '📚',
            'shopping': '🛒', 'other': '⭐',
        }
        return icons.get(self.category, '⭐')


class ChoreAssignment(models.Model):
    """A specific assignment of a chore to a child with due date."""
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed - Awaiting Approval'),
        (STATUS_APPROVED, 'Approved ✅'),
        (STATUS_REJECTED, 'Rejected ❌'),
    ]

    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='given_assignments')
    due_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_assignments')
    rejection_reason = models.CharField(max_length=200, blank=True)
    points_awarded = models.IntegerField(null=True, blank=True)
    note = models.TextField(blank=True, help_text="Note from kid when marking as done")

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.chore.title} → {self.assigned_to.display_name} [{self.status}]"

    @property
    def is_overdue(self):
        return self.status == self.STATUS_PENDING and self.due_date < timezone.now()

    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING

    @property
    def awaiting_approval(self):
        return self.status == self.STATUS_COMPLETED

    def mark_completed(self, note=''):
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.note = note
        self.save(update_fields=['status', 'completed_at', 'note'])

        # Sync to calendar assignments if present
        try:
            # Import here to avoid circular import at module import time
            from calendar_tasks.models import CalendarTaskAssignment
            for cal in getattr(self, 'calendar_assignments').all():
                # mark calendar assignment as completed for the child
                try:
                    cal.mark_completed(note=note)
                except Exception:
                    # Fallback: update fields directly
                    cal.status = CalendarTaskAssignment.STATUS_COMPLETED
                    cal.completed_at = timezone.now()
                    cal.note = note
                    cal.save(update_fields=['status', 'completed_at', 'note'])
        except Exception:
            # If calendar integration unavailable, ignore
            pass

    def approve(self, approved_by):
        """Approve the assignment and award points."""
        self.status = self.STATUS_APPROVED
        self.approved_at = timezone.now()
        self.approved_by = approved_by
        self.points_awarded = self.chore.points
        self.save(update_fields=['status', 'approved_at', 'approved_by', 'points_awarded'])
        self.assigned_to.add_points(
            self.chore.points,
            reason=f"Chore completed: {self.chore.title}",
            added_by=approved_by
        )
        # Check for badges
        self._check_badges()
        # Sync approval status to linked calendar assignments without re-awarding points
        try:
            from calendar_tasks.models import CalendarTaskAssignment
            for cal in getattr(self, 'calendar_assignments').all():
                cal.status = CalendarTaskAssignment.STATUS_APPROVED
                cal.approved_by = approved_by
                cal.approved_at = self.approved_at
                cal.save(update_fields=['status', 'approved_by', 'approved_at'])
        except Exception:
            pass

    def reject(self, approved_by, reason=''):
        self.status = self.STATUS_REJECTED
        self.approved_by = approved_by
        self.rejection_reason = reason
        self.save(update_fields=['status', 'approved_by', 'rejection_reason'])

    def _check_badges(self):
        """Award badges based on milestones."""
        from accounts.models import Badge
        kid = self.assigned_to
        completed_count = ChoreAssignment.objects.filter(
            assigned_to=kid, status=self.STATUS_APPROVED
        ).count()

        # First chore badge
        if completed_count == 1:
            Badge.objects.get_or_create(user=kid, badge_type='first_chore',
                                        defaults={'awarded_by': self.approved_by})

        # Points badges
        total_pts = kid.total_points
        for threshold, badge_type in [(100, 'points_100'), (500, 'points_500'), (1000, 'points_1000')]:
            if total_pts >= threshold:
                Badge.objects.get_or_create(user=kid, badge_type=badge_type,
                                            defaults={'awarded_by': self.approved_by})


class PointTransaction(models.Model):
    """Audit log of every point change."""
    TRANSACTION_TYPES = [
        ('chore', 'Chore Reward'),
        ('penalty', 'Penalty'),
        ('manual', 'Manual Adjustment'),
        ('payout', 'Pocket Money Payout'),
        ('bonus', 'Bonus'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions')
    points = models.IntegerField()
    reason = models.CharField(max_length=200, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='manual')
    balance_after = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    chore_assignment = models.OneToOneField(ChoreAssignment, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.points >= 0 else ''
        return f"{self.user.display_name}: {sign}{self.points} pts ({self.reason})"

    @property
    def is_positive(self):
        return self.points >= 0


class PocketMoneyPayout(models.Model):
    """Record of a pocket money payout to a child."""
    kid = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payouts')
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='made_payouts')
    points_at_payout = models.IntegerField()
    amount_euros = models.DecimalField(max_digits=8, decimal_places=2)
    note = models.TextField(blank=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    month = models.CharField(max_length=7)  # YYYY-MM format

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f"{self.kid.display_name}: {self.amount_euros}€ ({self.month})"
