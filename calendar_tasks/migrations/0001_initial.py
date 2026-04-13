# Generated migration file
# This is a placeholder. Run: python manage.py makemigrations calendar_tasks

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecurringChoreTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chore_title', models.CharField(help_text='Title of the recurring chore', max_length=150)),
                ('chore_description', models.TextField(blank=True)),
                ('points', models.IntegerField(help_text='Points for completing this chore')),
                ('category', models.CharField(choices=[('cleaning', '🧹 Cleaning'), ('cooking', '🍳 Cooking'), ('garden', '🌱 Garden'), ('laundry', '👕 Laundry'), ('pets', '🐾 Pets'), ('homework', '📚 Homework'), ('shopping', '🛒 Shopping'), ('other', '⭐ Other')], default='other', max_length=20)),
                ('frequency', models.CharField(choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='weekly', max_length=10)),
                ('days_of_week', models.CharField(blank=True, help_text='Comma-separated day numbers (0=Mon, 6=Sun) for weekly recurrence. Leave blank for all days.', max_length=20)),
                ('day_of_month', models.IntegerField(blank=True, help_text='Day of month for monthly recurrence', null=True)),
                ('scheduled_time', models.TimeField(default='09:00', help_text='Time of day to schedule the chore')),
                ('is_active', models.BooleanField(default=True)),
                ('start_date', models.DateField(default=django.utils.timezone.now)),
                ('end_date', models.DateField(blank=True, help_text='Leave blank for no end date', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_generated', models.DateTimeField(blank=True, help_text='Last time tasks were auto-generated', null=True)),
                ('assigned_to', models.ForeignKey(limit_choices_to={'role': 'child'}, on_delete=django.db.models.deletion.CASCADE, related_name='recurring_templates', to='accounts.user')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_recurring_templates', to='accounts.user')),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recurring_templates', to='accounts.family')),
            ],
            options={
                'verbose_name': 'Recurring Chore Template',
                'verbose_name_plural': 'Recurring Chore Templates',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SchedulePattern',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='e.g., Christmas, Summer Break', max_length=100)),
                ('pattern_type', models.CharField(choices=[('holiday', 'Holiday (no chores)'), ('special', 'Special Day (custom chores)'), ('break', 'Break Period (no chores)')], default='holiday', max_length=20)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_patterns', to='accounts.family')),
            ],
            options={
                'ordering': ['start_date'],
            },
        ),
        migrations.CreateModel(
            name='CalendarTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('description', models.TextField(blank=True)),
                ('points', models.IntegerField(help_text='Points for completing this task')),
                ('category', models.CharField(choices=[('cleaning', '🧹 Cleaning'), ('cooking', '🍳 Cooking'), ('garden', '🌱 Garden'), ('laundry', '👕 Laundry'), ('pets', '🐾 Pets'), ('homework', '📚 Homework'), ('shopping', '🛒 Shopping'), ('other', '⭐ Other')], default='other', max_length=20)),
                ('scheduled_date', models.DateField(help_text='Date the task is scheduled for')),
                ('scheduled_time', models.TimeField(help_text='Time the task should be completed')),
                ('due_time', models.TimeField(blank=True, help_text='Deadline time', null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed - Awaiting Approval'), ('approved', 'Approved ✅'), ('rejected', 'Rejected ❌'), ('skipped', 'Skipped')], default='pending', max_length=20)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.CharField(blank=True, max_length=200)),
                ('note', models.TextField(blank=True, help_text='Note from kid when marking as done')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_calendar_tasks', to='accounts.user')),
                ('assigned_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calendar_tasks', to='accounts.user')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_calendar_tasks', to='accounts.user')),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calendar_tasks', to='accounts.family')),
                ('recurring_template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generated_tasks', to='calendar_tasks.recurringchoretemplate')),
            ],
            options={
                'ordering': ['-scheduled_date', 'scheduled_time'],
            },
        ),
        migrations.AddIndex(
            model_name='calendartask',
            index=models.Index(fields=['family', 'scheduled_date'], name='calendar_ta_family_idx'),
        ),
        migrations.AddIndex(
            model_name='calendartask',
            index=models.Index(fields=['assigned_to', 'scheduled_date'], name='calendar_ta_assigne_idx'),
        ),
    ]

