# ChoreTracker - Developer Reference Guide

## 📋 File Structure

```
choretracker/
├── choretracker/                      # Django project config
│   ├── __init__.py                    # (Update with Celery import)
│   ├── settings.py                    # ✅ Updated with email & Celery config
│   ├── urls.py                        # ✅ Updated with calendar routes
│   ├── wsgi.py
│   ├── celery.py                      # ✅ NEW - Celery configuration
│   └── celery_init.py                 # ✅ Alternative init file
│
├── calendar_tasks/                    # ✅ NEW APP - Calendar & recurring chores
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── __init__.py
│   ├── admin.py                       # ✅ Admin interface
│   ├── apps.py
│   ├── forms.py                       # ✅ All forms for calendar features
│   ├── models.py                      # ✅ Models: RecurringChoreTemplate, CalendarTask, SchedulePattern
│   ├── tasks.py                       # ✅ Celery tasks
│   ├── urls.py                        # ✅ URL routing
│   └── views.py                       # ✅ All views
│
├── accounts/
│   ├── migrations/
│   │   └── 0002_user_password_reset.py # ✅ NEW - Password reset fields
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py                       # ✅ Updated with password reset forms
│   ├── models.py                      # ✅ Updated with password reset methods
│   ├── urls.py                        # ✅ Updated with password reset routes
│   └── views.py                       # ✅ Updated with password reset views
│
├── chores/                            # Existing - UNCHANGED
├── family/                            # Existing - UNCHANGED
├── dashboard/                         # Existing - UNCHANGED
│
├── templates/
│   ├── accounts/
│   │   ├── password_reset_request.html    # ✅ NEW
│   │   ├── password_reset.html            # ✅ NEW
│   │   └── ... (other existing templates)
│   ├── calendar_tasks/                    # ✅ NEW DIRECTORY
│   │   ├── calendar_view.html
│   │   ├── calendar_day_detail.html
│   │   ├── task_complete.html
│   │   ├── pending_task_approvals.html
│   │   ├── task_approve.html
│   │   ├── task_reject.html
│   │   ├── recurring_templates_list.html
│   │   ├── recurring_template_form.html
│   │   ├── recurring_template_confirm_delete.html
│   │   ├── create_calendar_task.html
│   │   ├── schedule_patterns_list.html
│   │   ├── schedule_pattern_form.html
│   │   ├── schedule_pattern_confirm_delete.html
│   │   └── delete_calendar_task.html
│   └── ... (other existing templates)
│
├── static/                            # Existing - UNCHANGED
├── SETUP_GUIDE.md                     # ✅ NEW - Detailed setup guide
├── QUICKSTART.md                      # ✅ NEW - Quick start guide
├── FEATURES_SUMMARY.md                # ✅ NEW - Feature overview
├── requirements.txt                   # ✅ Updated with new packages
├── README.md                          # Existing - can be updated
└── manage.py

```

---

## 🔌 Integration Points

### Django Views Decorator
```python
from chores.views import parent_required

@login_required
@parent_required
def parent_only_view(request):
    # Only parents can access
    pass
```

### Using in Templates
```django
{% if user.is_parent %}
    <!-- Parent-only content -->
{% endif %}

{% if user.is_child %}
    <!-- Child-only content -->
{% endif %}
```

### Celery Task Calling
```python
from calendar_tasks.tasks import send_approval_notification

# Async call (non-blocking)
send_approval_notification.delay(task_id)

# Sync call (blocking)
send_approval_notification(task_id)
```

### Email Sending
```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    subject='Title',
    message='Message body',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['user@example.com'],
)
```

---

## 🗂️ Model Relationships

```
Family
├── User (parent)
├── User (child)
├── RecurringChoreTemplate
│   └── CalendarTask (auto-generated)
├── CalendarTask (manual)
├── SchedulePattern
└── Chore (existing)

User
├── RecurringChoreTemplate (assigned_to)
├── CalendarTask (assigned_to)
├── PointTransaction
└── Badge

CalendarTask
├── RecurringChoreTemplate (source template, nullable)
├── assigned_to (User - child)
├── created_by (User - parent)
└── approved_by (User - parent, nullable)
```

---

## 🧪 Common Development Tasks

### Add a New Celery Task
```python
# In calendar_tasks/tasks.py
from celery import shared_task

@shared_task
def my_new_task(param):
    # Do work
    return result
```

### Add a Custom Manager
```python
# In models.py
class CalendarTaskManager(models.Manager):
    def pending_for_user(self, user):
        return self.filter(assigned_to=user, status=self.model.STATUS_PENDING)

class CalendarTask(models.Model):
    objects = CalendarTaskManager()
```

### Add Permission Checks
```python
# In views.py
@login_required
def view_task(request, task_id):
    task = get_object_or_404(CalendarTask, pk=task_id)
    
    # Check if user can view
    if not (task.family == request.user.family and 
            (request.user.is_parent or task.assigned_to == request.user)):
        messages.error(request, "You don't have permission.")
        return redirect('dashboard:home')
    
    return render(request, 'calendar_tasks/task_detail.html', {'task': task})
```

### Query Optimization
```python
# Bad - N+1 queries
tasks = CalendarTask.objects.all()
for task in tasks:
    print(task.assigned_to.display_name)  # Query per task!

# Good - Select related
tasks = CalendarTask.objects.select_related('assigned_to', 'created_by')
for task in tasks:
    print(task.assigned_to.display_name)  # No extra queries
```

---

## 🐛 Debugging Tips

### Check Celery Task Status
```bash
# In Django shell
from celery.result import AsyncResult
result = AsyncResult('task-id-here')
print(result.status)  # PENDING, STARTED, SUCCESS, FAILURE
print(result.result)  # Result or exception
```

### Manual Task Execution
```bash
python manage.py shell

from calendar_tasks.tasks import generate_recurring_tasks
result = generate_recurring_tasks()
print(result)
```

### Check Redis Connection
```bash
redis-cli ping  # Should return PONG
redis-cli keys '*'  # See all keys
redis-cli flushdb  # Clear all data (development only!)
```

### Email Testing
```python
# In Django shell
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test',
    'This is a test email.',
    settings.DEFAULT_FROM_EMAIL,
    ['test@example.com'],
)
# Should print to console if EMAIL_BACKEND is console.EmailBackend
```

---

## 📊 Performance Considerations

### Database Indexes
Already added on CalendarTask:
- (family, scheduled_date)
- (assigned_to, scheduled_date)

### Query Optimization
```python
# Avoid in loops
for task in tasks:
    count = task.assigned_to.calendar_tasks.count()  # BAD

# Use annotations
from django.db.models import Count
tasks = tasks.annotate(
    task_count=Count('assigned_to__calendar_tasks')
)
for task in tasks:
    count = task.task_count  # GOOD
```

### Caching
```python
from django.views.decorators.cache import cache_page

@cache_page(60)  # Cache for 60 seconds
def calendar_view(request):
    pass
```

---

## 🔒 Security Checklist

### Input Validation
✅ All forms use Django form validation
✅ Date/time inputs validated
✅ User permissions checked on all views
✅ CSRF tokens on all POST forms

### SQL Injection Prevention
✅ Using Django ORM (parameterized queries)
✅ Never using raw SQL with string concatenation

### XSS Prevention
✅ Auto-escaping in templates
✅ Using `|safe` filter only when necessary
✅ No user input in JavaScript

### CSRF Protection
✅ `{% csrf_token %}` on all forms
✅ `@csrf_exempt` not used

---

## 📈 Scaling Considerations

### Current Limitations
- Redis single instance
- Celery single worker
- Database queries not heavily optimized

### Scaling Steps
1. **Multiple Celery Workers:**
   ```bash
   celery -A choretracker worker -l info -c 4  # 4 processes
   ```

2. **Redis Cluster:**
   Use Sentinel or Cluster mode for high availability

3. **Database Replication:**
   Add read replicas for read-heavy queries

4. **Caching Layer:**
   Add Memcached for frequent queries

5. **Task Prioritization:**
   Use Celery priorities for urgent tasks

---

## 🚀 Deployment Checklist

### Before Deploy
- [ ] All tests passing
- [ ] Settings review (DEBUG=False, SECRET_KEY set)
- [ ] Email configured
- [ ] Redis server ready
- [ ] Static files collected
- [ ] Migrations tested on production database schema
- [ ] Backup database
- [ ] Document current state

### During Deploy
- [ ] Run migrations: `python manage.py migrate`
- [ ] Collect static: `python manage.py collectstatic --noinput`
- [ ] Start web server
- [ ] Start Celery worker
- [ ] Start Celery Beat

### After Deploy
- [ ] Test password reset email
- [ ] Create test calendar task
- [ ] Verify recurring task generation
- [ ] Check logs for errors
- [ ] Monitor Celery worker
- [ ] Test email notifications

---

## 📞 Support & Troubleshooting

### Common Issues

**Q: Celery tasks not executing?**
A: Check Redis is running, worker is listening, broker URL is correct

**Q: Email not sending?**
A: Check EMAIL_BACKEND, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD

**Q: Password reset link invalid?**
A: Check token expiration, database connectivity, Redis

**Q: Calendar tasks not generating?**
A: Check recurring template is_active, date range valid, Celery Beat running

### Getting Help
1. Check logs: `tail -f logs/celery.log`
2. Run tasks manually in shell
3. Check Redis: `redis-cli keys '*'`
4. Inspect database: Django admin or shell

---

## 🎯 Next Steps & Enhancements

### Suggested Improvements
1. **Calendar UI Enhancements:**
   - Drag-drop task scheduling
   - Week view
   - Multiple task colors/categories

2. **Notification Enhancements:**
   - SMS notifications
   - Push notifications
   - Notification preferences

3. **Reporting:**
   - Weekly reports to parents
   - Task completion analytics
   - Points trend analysis

4. **Mobile App:**
   - React Native app
   - REST API

5. **Advanced Scheduling:**
   - Conditional tasks (if previous task done, etc.)
   - Task dependencies
   - Time-based rules

---

**Happy Coding!** 🎉

