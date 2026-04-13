# ChoreTracker - New Features Setup Guide

This guide covers the new features added to ChoreTracker:
- **Recurring Chores** - Auto-generate chores on a schedule
- **Calendar System** - Time-based task scheduling
- **Schedule Customization** - Holidays, breaks, weekends
- **Password Reset** - For all account types
- **Email Notifications** - For task approvals and password resets

---

## 🔧 Prerequisites & Installation

### Step 1: Update Dependencies
```bash
pip install -r requirements.txt
```

The new dependencies added:
- `django-celery-beat==2.5.0` - Task scheduling
- `celery==5.4.0` - Background task queue
- `redis==5.0.1` - Message broker (or use RabbitMQ)

### Step 2: Install Redis (Message Broker)

**On Windows (using WSL2 or standalone Redis):**
```bash
# Using WSL2 (recommended)
wsl
sudo apt-get install redis-server
redis-server

# Or download standalone Redis from: https://github.com/microsoftarchive/redis/releases
```

**On macOS:**
```bash
brew install redis
redis-server
```

**On Linux:**
```bash
sudo apt-get install redis-server
redis-server
```

### Step 3: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates new tables for:
- `calendar_tasks.RecurringChoreTemplate`
- `calendar_tasks.CalendarTask`
- `calendar_tasks.SchedulePattern`
- Updated `accounts.User` with password reset fields

### Step 4: Environment Variables

Update or create `.env` file with email configuration:

```bash
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@choretracker.com

# Celery Configuration
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

**For Gmail:**
1. Enable 2-Factor Authentication
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password in `EMAIL_HOST_PASSWORD`

### Step 5: Run Celery and Celery Beat

Open two separate terminal windows:

**Terminal 1 - Celery Worker:**
```bash
celery -A choretracker worker -l info
```

**Terminal 2 - Celery Beat Scheduler:**
```bash
celery -A choretracker beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Or run both together:
```bash
celery -A choretracker worker -B -l info
```

---

## 📅 Feature Guides

### 1. Recurring Chores

Create chores that automatically generate assignments for kids.

#### Creating a Recurring Chore
1. Go to **Calendar → Recurring Chores**
2. Click **+ Create Recurring Chore**
3. Fill in:
   - **Chore Title** - Name of the task
   - **Description** - Optional details
   - **Points** - Reward points
   - **Category** - Type of chore
   - **Assigned to** - Select child
   - **Frequency** - Daily, Weekly, or Monthly
   - **Days of Week** - For weekly (e.g., "0,1,2,3,4" for Mon-Fri)
   - **Day of Month** - For monthly (e.g., 15)
   - **Scheduled Time** - What time of day
   - **Valid From/To** - Date range

#### How It Works
- Every day at midnight (configurable), Celery Beat runs the task generator
- For each active recurring template, it checks if a task should be created
- Tasks are generated for tomorrow's date if it matches the recurrence pattern
- Auto-generated tasks appear on the Calendar

#### Example: Daily after-school chore
- Frequency: Daily
- Time: 17:00 (5 PM)
- Valid: Forever

#### Example: Weekday homework check
- Frequency: Weekly
- Days: 0,1,2,3,4 (Monday-Friday)
- Time: 18:00 (6 PM)

---

### 2. Calendar System

View and manage tasks by date with time scheduling.

#### For Parents:
1. **Create Manual Tasks:**
   - Calendar → + Add Task
   - Assign to specific child
   - Set date and time
   - Optionally set a due time

2. **Create Recurring Tasks:**
   - Calendar → Recurring Chores
   - Create recurring templates
   - Tasks generate automatically

3. **Review Pending Approvals:**
   - Calendar → Pending Task Approvals
   - View tasks kids marked as complete
   - Approve (award points) or Reject

4. **Schedule Patterns:**
   - Calendar → Schedule Patterns
   - Create holidays (no chores)
   - Create special days (custom rules)
   - Create breaks (vacation periods)

#### For Kids:
1. **View Calendar:**
   - Navigate to their calendar
   - See all tasks scheduled for them
   - View by month or day

2. **Complete Tasks:**
   - Click on pending task
   - Click "Mark as Complete"
   - Add optional note
   - Submit for approval

3. **Track Status:**
   - Pending: Waiting to complete
   - Awaiting Approval: Done, waiting for parent
   - Approved: ✅ Points awarded
   - Rejected: ❌ Try again

---

### 3. Schedule Patterns (Holidays, Breaks)

Customize the schedule for special periods.

#### Creating a Pattern:
1. Go to **Calendar → Schedule Patterns**
2. Click **+ Add Pattern**
3. Choose type:
   - **Holiday** - No chores scheduled (Christmas, etc.)
   - **Break** - No chores (summer vacation, etc.)
   - **Special** - Custom chores (e.g., spring cleaning week)
4. Set start and end dates
5. Save

#### How They Work:
- When creating/recurring tasks, check active patterns
- Holiday/Break patterns: Skip task generation
- Special patterns: Allow custom task rules

---

### 4. Password Reset

All users can reset their password via email.

#### For Users:
1. Go to **Login** page
2. Click **"Forgot Password?"** link
3. Enter username or email
4. Check email for reset link
5. Click link and enter new password
6. Link expires after 24 hours

#### For Parents (Enabling Email):
- Ensure `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are configured in `.env`
- Test by requesting a password reset

#### Security:
- Reset tokens are unique UUIDs
- Tokens expire after 24 hours
- One-time use tokens are cleared after use
- Email backend can be console (development) or SMTP (production)

---

### 5. Email Notifications

Parents receive emails when kids complete tasks.

#### When Emails Are Sent:
1. **Task Completion Notification:**
   - Kid marks calendar task as complete
   - Email sent to all parents in family
   - Includes task details and kid's note

2. **Password Reset Email:**
   - User requests password reset
   - Email with 24-hour reset link sent
   - Valid for one-time use only

#### Email Configuration:

**Development Mode (Console Output):**
```bash
# In .env:
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```
Emails print to console instead of sending.

**Production Mode (Gmail SMTP):**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@choretracker.com
```

**Other Email Providers:**
Similar setup for SendGrid, AWS SES, Office365, etc.

---

## 🚀 Running in Production

### Using Gunicorn + Celery + Redis

1. **Install Production Dependencies:**
```bash
pip install gunicorn
```

2. **Start Web Server:**
```bash
gunicorn choretracker.wsgi:application --bind 0.0.0.0:8000
```

3. **Start Celery Worker:**
```bash
celery -A choretracker worker -l info
```

4. **Start Celery Beat:**
```bash
celery -A choretracker beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Using Docker (Recommended)

Create `docker-compose.yml`:
```yaml
version: '3'

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: gunicorn choretracker.wsgi:application --bind 0.0.0.0:8000
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=...
      - SECRET_KEY=...
    depends_on:
      - redis

  celery_worker:
    build: .
    command: celery -A choretracker worker -l info
    environment:
      - DATABASE_URL=...
      - SECRET_KEY=...
    depends_on:
      - redis

  celery_beat:
    build: .
    command: celery -A choretracker beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DATABASE_URL=...
      - SECRET_KEY=...
    depends_on:
      - redis
```

---

## 🧪 Testing

### Test Recurring Task Generation:
```bash
python manage.py shell
>>> from calendar_tasks.tasks import generate_recurring_tasks
>>> result = generate_recurring_tasks()
>>> print(result)
```

### Test Email Sending:
```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> from django.conf import settings
>>> send_mail(
...     'Test Email',
...     'This is a test.',
...     settings.DEFAULT_FROM_EMAIL,
...     ['your-email@example.com'],
... )
```

### Check Celery Status:
```bash
celery -A choretracker inspect active
celery -A choretracker inspect scheduled
```

---

## 🔍 Troubleshooting

### Celery not running tasks:
1. Check Redis is running: `redis-cli ping` (should return PONG)
2. Check Celery worker log for errors
3. Verify `CELERY_BROKER_URL` in settings
4. Restart both Celery worker and Beat

### Email not sending:
1. Check `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env`
2. Verify email provider SMTP settings
3. Check email backend: `console` for dev, `smtp` for prod
4. Look for errors in Django logs

### Password reset link not working:
1. Ensure user has valid email in database
2. Check Redis is storing tokens correctly
3. Verify email body contains correct URL
4. Check token hasn't expired (24 hours)

### Calendar tasks not generating:
1. Check Celery Beat is running
2. Verify recurring template is active and within date range
3. Check Celery worker is processing tasks
4. Run `generate_recurring_tasks()` manually to debug

---

## 📊 Database Schema

### New Models:

**RecurringChoreTemplate**
- Defines reusable chore patterns (daily/weekly/monthly)
- Linked to family and child
- Auto-generates CalendarTask instances

**CalendarTask**
- Individual task scheduled for specific date/time
- Status: pending → completed → approved/rejected
- Can be auto-generated or manually created

**SchedulePattern**
- Represents holidays, breaks, or special schedules
- Type: holiday (skip chores) or special (custom rules)
- Covers date ranges

---

## 📝 API Endpoints

### Calendar Tasks Views:
```
/calendar/                              - View calendar (month)
/calendar/<year>/<month>/<day>/         - View day details
/calendar/task/create/                  - Create manual task
/calendar/task/<id>/complete/           - Mark task complete
/calendar/approvals/                    - Pending approvals (parent)
/calendar/task/<id>/approve/            - Approve task (parent)
/calendar/task/<id>/reject/             - Reject task (parent)
/calendar/recurring/                    - List recurring chores
/calendar/recurring/create/             - Create recurring chore
/calendar/patterns/                     - List schedule patterns
/calendar/patterns/create/              - Create pattern
```

### Password Reset Views:
```
/accounts/password-reset/               - Request reset
/accounts/password-reset/<token>/       - Reset with token
```

---

## 🤝 Support

For issues or questions:
1. Check logs: Django debug log, Celery worker output
2. Verify environment variables
3. Ensure Redis is running
4. Check database migrations ran successfully

Happy tasking! 🎉

