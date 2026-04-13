# ChoreTracker - Quick Reference Commands

## 🚀 Quick Start

### First Time Setup (5 minutes)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Create superuser (optional)
python manage.py createsuperuser
```

### Running Development Environment

**Terminal 1 - Redis (Message Broker)**
```bash
redis-server
```

**Terminal 2 - Celery Worker & Beat**
```bash
celery -A choretracker worker -B -l info
```

**Terminal 3 - Django Server**
```bash
python manage.py runserver
```

Access at: http://127.0.0.1:8000

---

## 🧪 Testing Commands

### Test Recurring Task Generation
```bash
python manage.py shell
>>> from calendar_tasks.tasks import generate_recurring_tasks
>>> result = generate_recurring_tasks()
>>> print(result)
```

### Test Email in Development
```bash
# Should already be set to console backend
# Emails will print in terminal output
```

### Create Test Data
```bash
python manage.py shell
>>> from accounts.models import Family, User
>>> from calendar_tasks.models import RecurringChoreTemplate, CalendarTask
>>> 
>>> # Create family
>>> family = Family.objects.create(name="Test Family")
>>> 
>>> # Create parent
>>> parent = User.objects.create_user(
...     username="parent",
...     password="password",
...     first_name="Parent",
...     family=family,
...     role="parent"
... )
>>> 
>>> # Create child
>>> child = User.objects.create_user(
...     username="child",
...     password="password",
...     first_name="Child",
...     family=family,
...     role="child",
...     avatar="🦁"
... )
>>>
>>> # Create recurring chore
>>> recurring = RecurringChoreTemplate.objects.create(
...     family=family,
...     chore_title="Daily Homework",
...     points=50,
...     frequency="daily",
...     assigned_to=child,
...     created_by=parent
... )
```

### Run Management Commands
```bash
# Make migrations (if you modify models)
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Collect static files (for production)
python manage.py collectstatic --noinput

# Clear cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

---

## 🔍 Debugging Commands

### Check Celery Status
```bash
# List active tasks
celery -A choretracker inspect active

# List scheduled tasks
celery -A choretracker inspect scheduled

# Check worker stats
celery -A choretracker inspect stats
```

### Check Redis
```bash
# Ping Redis
redis-cli ping

# See all keys
redis-cli keys '*'

# Get key value
redis-cli get <key>

# Clear all data
redis-cli flushdb

# Monitor in real-time
redis-cli monitor
```

### Django Shell Debugging
```bash
python manage.py shell

# Check recurring templates
>>> from calendar_tasks.models import RecurringChoreTemplate
>>> RecurringChoreTemplate.objects.all()

# Check calendar tasks
>>> from calendar_tasks.models import CalendarTask
>>> CalendarTask.objects.all()

# Check pending approvals
>>> from calendar_tasks.models import CalendarTask
>>> CalendarTask.objects.filter(status='completed')

# Generate tasks manually
>>> from calendar_tasks.tasks import generate_recurring_tasks
>>> generate_recurring_tasks()
```

---

## 📧 Email Testing

### Console Backend (Development)
Already configured. Emails print to terminal.

### Gmail SMTP Setup
1. Enable 2-Factor Authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Add to .env:
```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

### Test Email Sending
```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail(
...     "Test Email",
...     "This is a test",
...     "noreply@choretracker.com",
...     ["test@example.com"]
... )
```

---

## 🗂️ File Locations

### Templates
```
templates/
├── accounts/
│   ├── password_reset_request.html
│   └── password_reset.html
└── calendar_tasks/
    ├── calendar_view.html
    ├── calendar_day_detail.html
    ├── task_complete.html
    ├── pending_task_approvals.html
    ├── task_approve.html
    ├── task_reject.html
    ├── create_calendar_task.html
    ├── delete_calendar_task.html
    ├── recurring_templates_list.html
    ├── recurring_template_form.html
    ├── recurring_template_confirm_delete.html
    ├── schedule_patterns_list.html
    ├── schedule_pattern_form.html
    └── schedule_pattern_confirm_delete.html
```

### Apps
```
calendar_tasks/
├── migrations/
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── tasks.py
├── urls.py
└── views.py
```

### Documentation
```
├── SETUP_GUIDE.md
├── QUICKSTART.md
├── FEATURES_SUMMARY.md
├── DEVELOPER_GUIDE.md
├── IMPLEMENTATION_CHECKLIST.md
└── QUICK_REFERENCE.md (this file)
```

---

## 🔐 Environment Variables Template

```bash
# Django
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/choretracker

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@choretracker.com

# Celery
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

---

## 🐳 Docker Commands

### Run with Docker Compose
```bash
docker-compose up -d
docker-compose down
docker-compose logs -f
docker-compose exec web python manage.py migrate
```

### Build Docker Image
```bash
docker build -t choretracker .
docker run -p 8000:8000 choretracker
```

---

## 📊 Admin Interface

Access at: http://127.0.0.1:8000/admin/

### Models Available
- Users
- Families
- Recurring Chore Templates
- Calendar Tasks
- Schedule Patterns
- Chores (existing)
- Chore Assignments (existing)

---

## 🚀 Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn choretracker.wsgi:application --bind 0.0.0.0:8000
```

### Using Supervisor (for background tasks)
```ini
[program:choretracker-celery-worker]
command=celery -A choretracker worker -l info
directory=/path/to/choretracker
user=www-data
numprocs=1
stdout_logfile=/var/log/choretracker/celery-worker.log
stderr_logfile=/var/log/choretracker/celery-worker.log
autostart=true
autorestart=true

[program:choretracker-celery-beat]
command=celery -A choretracker beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=/path/to/choretracker
user=www-data
numprocs=1
stdout_logfile=/var/log/choretracker/celery-beat.log
stderr_logfile=/var/log/choretracker/celery-beat.log
autostart=true
autorestart=true
```

---

## 🆘 Troubleshooting

### Celery Not Working
```bash
# Check if Redis is running
redis-cli ping  # Should return PONG

# Check Celery worker log
celery -A choretracker inspect active

# Restart everything
pkill -f celery
redis-cli flushdb
redis-server
celery -A choretracker worker -B -l info
```

### Email Not Sending
```bash
# Check EMAIL_BACKEND setting
# Should be 'django.core.mail.backends.console.EmailBackend' for dev
# Should be 'django.core.mail.backends.smtp.EmailBackend' for production

# Test manually in shell
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test body', 'from@example.com', ['to@example.com'])
```

### Calendar Tasks Not Generating
```bash
# Check recurring template is active
python manage.py shell
>>> from calendar_tasks.models import RecurringChoreTemplate
>>> t = RecurringChoreTemplate.objects.first()
>>> t.is_active  # Should be True

# Check date range
>>> t.start_date  # Should be today or earlier
>>> t.end_date  # Should be None or future

# Run generator manually
>>> from calendar_tasks.tasks import generate_recurring_tasks
>>> generate_recurring_tasks()
```

---

## 📝 Git Workflow

```bash
# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Add calendar features"

# Push
git push origin main

# Create branch
git checkout -b feature/calendar-improvements
```

---

## 🔄 Migration Workflow

```bash
# Make changes to models
# Then:
python manage.py makemigrations

# Review migration file
cat calendar_tasks/migrations/XXXX_name.py

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback
python manage.py migrate calendar_tasks 0001
```

---

## 💡 Useful Shortcuts

### Django Shell Shortcuts
```python
# Quick import shortcut
from django.shortcuts import *
from calendar_tasks.models import *

# Query all objects
CalendarTask.objects.all()

# Filter
CalendarTask.objects.filter(status='pending')

# Get or create
obj, created = CalendarTask.objects.get_or_create(id=1)

# Update
CalendarTask.objects.filter(id=1).update(status='approved')

# Delete
CalendarTask.objects.filter(id=1).delete()
```

### Django Shell Enhancements
```bash
# Use IPython shell (if installed)
pip install ipython
python manage.py shell

# Or use Django extensions
pip install django-extensions
python manage.py shell_plus  # Auto imports
```

---

## 📞 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Redis connection refused | `redis-server` not running - start it |
| Celery tasks not running | Check worker is listening, broker URL correct |
| Email not sending | Check EMAIL_BACKEND, credentials |
| Password reset link 404 | Check token was generated, database synced |
| Calendar not showing | Check migrations ran, recurring template created |
| Permission denied | Check user is parent, has family |
| CSRF token error | Check form has {% csrf_token %}, POST method |

---

## 📚 Documentation Reference

**For Setup Instructions:**
→ SETUP_GUIDE.md

**For Quick Deployment:**
→ QUICKSTART.md

**For Feature Details:**
→ FEATURES_SUMMARY.md

**For Development:**
→ DEVELOPER_GUIDE.md

**For Project Status:**
→ IMPLEMENTATION_CHECKLIST.md

---

**Happy Coding! 🚀**

Last Updated: April 12, 2026
ChoreTracker v2.0 with Calendar System

