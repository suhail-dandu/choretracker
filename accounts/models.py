from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class Family(models.Model):
    name = models.CharField(max_length=100)
    invite_code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    currency_symbol = models.CharField(max_length=5, default='€')
    points_per_unit = models.IntegerField(default=100, help_text="Points needed for 1 currency unit")

    class Meta:
        verbose_name_plural = "Families"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.invite_code:
            import random, string
            self.invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)


class User(AbstractUser):
    ROLE_PARENT = 'parent'
    ROLE_CHILD = 'child'
    ROLE_CHOICES = [
        (ROLE_PARENT, 'Parent'),
        (ROLE_CHILD, 'Child'),
    ]

    AVATAR_CHOICES = [
        ('🦁', 'Lion'),
        ('🐯', 'Tiger'),
        ('🦊', 'Fox'),
        ('🐻', 'Bear'),
        ('🐼', 'Panda'),
        ('🐨', 'Koala'),
        ('🦄', 'Unicorn'),
        ('🐸', 'Frog'),
        ('🐙', 'Octopus'),
        ('🦋', 'Butterfly'),
        ('🐬', 'Dolphin'),
        ('🦅', 'Eagle'),
    ]

    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_CHILD)
    avatar = models.CharField(max_length=10, choices=AVATAR_CHOICES, default='🦁')
    date_of_birth = models.DateField(null=True, blank=True)
    total_points = models.IntegerField(default=0)
    total_earned_lifetime = models.IntegerField(default=0)

    # Password reset fields
    password_reset_token = models.CharField(max_length=100, blank=True, null=True, unique=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['first_name']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_parent(self):
        return self.role == self.ROLE_PARENT

    @property
    def is_child(self):
        return self.role == self.ROLE_CHILD

    @property
    def points_as_money(self):
        if self.family:
            return self.total_points / self.family.points_per_unit
        return self.total_points / 100

    @property
    def display_name(self):
        return self.first_name or self.username

    def add_points(self, points, reason='', added_by=None):
        """Add or deduct points and log the transaction."""
        from chores.models import PointTransaction
        self.total_points += points
        if points > 0:
            self.total_earned_lifetime += points
        self.save(update_fields=['total_points', 'total_earned_lifetime'])
        PointTransaction.objects.create(
            user=self,
            points=points,
            reason=reason,
            created_by=added_by,
            balance_after=self.total_points,
        )
        return self.total_points

    def generate_password_reset_token(self):
        """Generate a unique password reset token."""
        from django.utils import timezone
        self.password_reset_token = str(uuid.uuid4())
        self.password_reset_expires = timezone.now() + timezone.timedelta(hours=24)
        self.save(update_fields=['password_reset_token', 'password_reset_expires'])
        return self.password_reset_token

    def is_password_reset_token_valid(self):
        """Check if password reset token is valid."""
        from django.utils import timezone
        if not self.password_reset_token:
            return False
        return self.password_reset_expires > timezone.now()

    def clear_password_reset_token(self):
        """Clear the password reset token."""
        self.password_reset_token = None
        self.password_reset_expires = None
        self.save(update_fields=['password_reset_token', 'password_reset_expires'])


class Badge(models.Model):
    BADGE_TYPES = [
        ('first_chore', '🌟 First Chore'),
        ('streak_3', '🔥 3-Day Streak'),
        ('streak_7', '⚡ 7-Day Streak'),
        ('points_100', '💯 100 Points'),
        ('points_500', '🏆 500 Points'),
        ('points_1000', '👑 1000 Points'),
        ('perfect_week', '🎯 Perfect Week'),
        ('helper', '🤝 Super Helper'),
        ('early_bird', '🌅 Early Bird'),
        ('champion', '🥇 Champion'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge_type = models.CharField(max_length=50, choices=BADGE_TYPES)
    awarded_at = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='awarded_badges')

    class Meta:
        unique_together = ('user', 'badge_type')

    def __str__(self):
        return f"{self.badge_type} - {self.user.display_name}"

    @property
    def display(self):
        return dict(self.BADGE_TYPES).get(self.badge_type, self.badge_type)
