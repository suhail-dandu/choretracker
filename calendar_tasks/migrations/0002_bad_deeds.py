from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('calendar_tasks', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BadDeed',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Name of the bad deed', max_length=150)),
                ('description', models.TextField(blank=True)),
                ('negative_points', models.IntegerField(help_text='Points to deduct (enter positive number, will be negated)', validators=[django.core.validators.MinValueValidator(1)])),
                ('category', models.CharField(choices=[('behavior', '😠 Bad Behavior'), ('attitude', '😤 Bad Attitude'), ('disrespect', '🤨 Disrespect'), ('disobedience', '⛔ Disobedience'), ('lying', '🤥 Lying'), ('fighting', '👊 Fighting'), ('laziness', '😴 Laziness'), ('other', '⚠️ Other')], default='other', max_length=20)),
                ('is_recurring', models.BooleanField(default=False)),
                ('frequency', models.CharField(blank=True, choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='weekly', max_length=10)),
                ('days_of_week', models.CharField(blank=True, help_text='Comma-separated day numbers (0=Mon, 6=Sun) for weekly recurrence', max_length=20)),
                ('day_of_month', models.IntegerField(blank=True, help_text='Day of month for monthly', null=True)),
                ('scheduled_time', models.TimeField(default='09:00', help_text='Time of day for calendar')),
                ('is_active', models.BooleanField(default=True)),
                ('start_date', models.DateField(default=django.utils.timezone.now)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_applied', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(help_text='Child assigned to this bad deed', limit_choices_to={'role': 'child'}, on_delete=django.db.models.deletion.CASCADE, related_name='bad_deeds_assigned', to='accounts.user')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_bad_deeds', to='accounts.user')),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bad_deeds', to='accounts.family')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BadDeedInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('description', models.TextField(blank=True)),
                ('negative_points', models.IntegerField()),
                ('category', models.CharField(choices=[('behavior', '😠 Bad Behavior'), ('attitude', '😤 Bad Attitude'), ('disrespect', '🤨 Disrespect'), ('disobedience', '⛔ Disobedience'), ('lying', '🤥 Lying'), ('fighting', '👊 Fighting'), ('laziness', '😴 Laziness'), ('other', '⚠️ Other')], default='other', max_length=20)),
                ('reason', models.TextField(help_text='Reason for deduction')),
                ('created_date', models.DateField(auto_now_add=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('active', 'Active (Points Deducted)'), ('removed', 'Removed (Points Restored)')], default='active', max_length=20)),
                ('removed_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bad_deed_instances', to='accounts.user')),
                ('bad_deed', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='instances', to='calendar_tasks.baddeed')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_bad_deed_instances', to='accounts.user')),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bad_deed_instances', to='accounts.family')),
                ('removed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='removed_bad_deeds', to='accounts.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

