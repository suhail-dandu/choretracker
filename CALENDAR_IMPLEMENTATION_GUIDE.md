# Calendar Tasks - Fix Implementation Guide

## Issue
Tasks and recurring tasks were created successfully but NOT appearing in the calendar view for both parents and children.

## Root Cause
**Template Bug:** Line 67 of `templates/calendar_tasks/calendar_view.html` was using:
```html
{% if date_str == day.isoformat %}
```

In Django templates, you **cannot call methods directly** on objects. The `.isoformat()` method was never executed, causing the date comparison to always fail. The template was trying to compare:
- Left side: `"2026-04-13"` (string from dictionary key)
- Right side: `<datetime.date object>` (not a string!)

This mismatch meant tasks never matched their dates and were never displayed.

## Solution

### Primary Fix: Template (calendar_view.html)
Changed line 67 from:
```html
{% if date_str == day.isoformat %}
```

To:
```html
{% if date_str == day|date:"Y-m-d" %}
```

This uses Django's `date` filter to format the date object to the same ISO format string as the dictionary keys.

### Secondary Enhancement: Management Command
Created `calendar_tasks/management/commands/generate_tasks.py` for generating:
- Recurring chore tasks
- Bad deed calendar entries
- Handles daily, weekly, and monthly recurrence

## How Calendar Display Works

### Data Flow (Backend)
1. **calendar_view** in `views.py`:
   - Queries CalendarTask objects for the requested month
   - Filters by family and user role (child-specific or all)
   - Groups tasks by date using `task.scheduled_date.isoformat()` as key (e.g., `"2026-04-13"`)
   - Passes to template: `tasks_by_date` dict and `all_tasks_items` list of tuples

2. **Template Rendering** in `calendar_view.html`:
   - Generates calendar grid with all days of the month
   - For each calendar day, iterates through `all_tasks_items`
   - Compares `date_str` (ISO string like `"2026-04-13"`) with `day|date:"Y-m-d"` (formatted date)
   - When dates match, displays all tasks for that day as color-coded badges

### Template Logic
```html
{% for day in calendar_days %}
    {% for date_str, task_list in all_tasks_items %}
        {% if date_str == day|date:"Y-m-d" %}
            <!-- Display tasks here -->
            {% for task in task_list %}
                <span class="badge bg-[color]">{{ task.title }}</span>
            {% endfor %}
        {% endif %}
    {% endfor %}
{% endfor %}
```

## Task Status Colors
- **Blue badge** (`bg-info`): Pending
- **Yellow/Orange badge** (`bg-warning`): Completed - Awaiting Approval
- **Green badge** (`bg-success`): Approved
- **Red badge** (`bg-danger`): Rejected

## User Visibility Rules
- **Parents**: See all tasks in their family
- **Children**: See only tasks assigned to them

## Testing the Fix

### Test 1: Create Manual Calendar Task
```
1. Login as parent
2. Go to Calendar menu
3. Click "Add Task" button
4. Fill form:
   - Title: "Test Task"
   - Child: Select a child
   - Date: Today or any date
   - Points: 10
5. Save
6. Verify task appears on calendar
```

### Test 2: Create Recurring Task
```
1. Login as parent
2. Go to Calendar → Recurring Chores
3. Click "Create Recurring Chore"
4. Fill form with:
   - Title: "Weekly Cleaning"
   - Child: Select a child
   - Frequency: Weekly
   - Days: Monday-Friday (0,1,2,3,4)
   - Points: 25
5. Save
6. Generate tasks with command:
   python manage.py generate_tasks --days 30 --today
7. View calendar - should see tasks on correct days
```

### Test 3: Verify Child View
```
1. Login as child
2. Go to Calendar
3. Should see only tasks assigned to them
4. Tasks should match scheduled dates
```

### Test 4: Run Verification Script
```bash
cd C:\Projects\choretracker
python test_calendar_fix.py
```

## Files Changed

### Modified
- `templates/calendar_tasks/calendar_view.html` - Fixed date filter on line 67

### Created
- `calendar_tasks/management/__init__.py`
- `calendar_tasks/management/commands/__init__.py`
- `calendar_tasks/management/commands/generate_tasks.py` - Task generation command
- `CALENDAR_FIX_SUMMARY.md` - Quick reference
- `test_calendar_fix.py` - Verification script

## Important Notes

1. **Celery Task Limitation**: The `generate_recurring_tasks` Celery task only generates tasks for **tomorrow**. For immediate display, use the management command.

2. **Task Generation**: Recurring tasks must be generated separately from template creation. The template only defines the pattern; tasks are created on demand.

3. **Date Range**: The calendar view automatically handles displaying tasks from:
   - Previous month (faded out)
   - Current month
   - Next month (if needed for calendar grid)

4. **Legacy Tasks**: Historic tasks from past months should display correctly when navigating back to those months.

## Debugging Tips

If tasks still don't appear:

1. **Check Database**:
   ```bash
   python manage.py shell
   >>> from calendar_tasks.models import CalendarTask
   >>> CalendarTask.objects.count()  # Should have tasks
   >>> CalendarTask.objects.values_list('scheduled_date', 'title')[:5]
   ```

2. **Check Family Assignment**:
   ```python
   >>> task = CalendarTask.objects.first()
   >>> task.family == request.user.family  # Should be True
   ```

3. **Check Date Range**:
   ```python
   >>> from datetime import date
   >>> task.scheduled_date >= date(2026, 4, 1)
   >>> task.scheduled_date <= date(2026, 4, 30)
   ```

4. **Test Template Rendering**:
   ```bash
   python test_calendar_fix.py
   ```

## Verification Checklist
- [ ] Manual calendar tasks appear on correct dates
- [ ] Recurring tasks appear after running management command
- [ ] Tasks display for both parent and child accounts
- [ ] Task status colors display correctly
- [ ] Month navigation works
- [ ] Children see only their tasks
- [ ] Parents see all family tasks

