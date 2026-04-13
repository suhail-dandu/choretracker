# Quick Start Guide - New Features

## 🚀 5-Minute Setup

### 1. Install and Migrate
```bash
pip install -r requirements.txt
python manage.py migrate
```

### 2. Start Redis
```bash
# In one terminal
redis-server
```

### 3. Start Celery Workers
```bash
# In second terminal
celery -A choretracker worker -B -l info
```

### 4. Run Django Server
```bash
# In third terminal
python manage.py runserver
```

### 5. Configure Email (Optional)
Add to `.env`:
```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```
This prints emails to console instead of sending them.

---

## 📅 Try the Calendar Feature

### As a Parent:

1. **View Calendar:**
   - Login → Dashboard → Click "📅 Calendar" in navigation

2. **Create a Recurring Chore:**
   - Calendar → "🔄 Recurring Chores" → "➕ Create"
   - Title: "Daily Homework"
   - Frequency: Daily
   - Time: 18:00
   - Assign to: Your kid
   - Save

3. **Create Manual Task:**
   - Calendar → "➕ Add Task"
   - Select a kid
   - Set date and time
   - Save

4. **View Pending Approvals:**
   - Calendar → "Pending Task Approvals"
   - See tasks kids submitted
   - Approve or Reject

### As a Kid:

1. **View Your Calendar:**
   - Login → Dashboard → Click "📅 Calendar"

2. **Complete a Task:**
   - Click "Mark Complete" on pending task
   - Add optional note
   - Submit

3. **Check Status:**
   - View task status updates
   - Get approved/rejected notification

---

## 🔐 Try Password Reset

1. **Logout**
2. **Go to Login page**
3. **Click "Forgot Password?"**
4. Enter username or email
5. **Check console output** (emails print there in development)
6. **Click the reset link** in the console output
7. Enter new password
8. Login with new password

---

## 📊 Admin Panel

View new models in Django admin:

```
/admin/calendar_tasks/recurringchoretemplate/
/admin/calendar_tasks/calendartask/
/admin/calendar_tasks/schedulepattern/
```

Create and manage tasks directly from admin (useful for testing).

---

## 🧪 Test Recurring Task Generation

```bash
python manage.py shell
```

Then in the Python shell:
```python
from calendar_tasks.tasks import generate_recurring_tasks
result = generate_recurring_tasks()
print(result)  # Should see: "Generated X recurring tasks"
```

---

## 🎯 Key Features Checklist

- [x] Recurring chores auto-generate daily
- [x] Calendar view by month and day
- [x] Parents can create manual tasks
- [x] Kids can complete and submit tasks
- [x] Parents can approve/reject tasks
- [x] Points awarded only after approval
- [x] Email notifications (on completion)
- [x] Password reset via email
- [x] Schedule patterns for holidays

---

## 🆘 Quick Troubleshooting

**Celery tasks not running?**
- Check Redis: `redis-cli ping` → should see `PONG`
- Restart Celery worker: `Ctrl+C` then rerun command

**Email not sending?**
- Check `EMAIL_BACKEND` in settings
- For development, set to `console.EmailBackend`
- Emails appear in terminal output

**Calendar tasks not appearing?**
- Ensure Celery Beat is running (with `-B` flag)
- Check `is_active=True` on recurring template
- Verify date range (`start_date` and `end_date`)

---

## 📚 Full Documentation

See `SETUP_GUIDE.md` for:
- Detailed setup instructions
- Production deployment
- Email provider configuration
- Database schema details
- API endpoints

---

## 💡 Pro Tips

1. **Test Email in Development:**
   Use `console.EmailBackend` to see emails in terminal

2. **Speed Up Task Generation:**
   Manually run: `python manage.py shell` → `generate_recurring_tasks()`

3. **Monitor Celery:**
   Use `celery -A choretracker inspect active` to see running tasks

4. **Debug Templates:**
   Check browser's Network tab to see template variables passed

---

Enjoy the new features! 🎉

