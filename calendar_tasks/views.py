from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import CalendarTask, RecurringChoreTemplate, SchedulePattern, BadDeed, BadDeedInstance
from .forms import (
    CalendarTaskForm, CalendarTaskCompleteForm, CalendarTaskRejectForm,
    RecurringChoreTemplateForm, SchedulePatternForm, BadDeedForm, BadDeedInstanceForm
)
from .tasks import send_approval_notification
from accounts.models import User


def parent_required(view_func):
    """Decorator: restrict to parent role."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_parent:
            messages.error(request, "Only parents can do that! 🔒")
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def _generate_recurring_tasks_for_month(family, start_date, end_date):
    """Generate recurring tasks for a month if they don't exist."""
    from django.db import models

    # Get all active templates for this family
    templates = RecurringChoreTemplate.objects.filter(
        family=family,
        is_active=True,
        start_date__lte=end_date
    )

    # Filter by end_date if set
    templates = templates.filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=start_date)
    )

    for template in templates:
        # Determine dates to create tasks for
        dates_to_create = []

        if template.frequency == 'daily':
            current = start_date
            while current <= end_date:
                dates_to_create.append(current)
                current += timedelta(days=1)

        elif template.frequency == 'weekly':
            if template.days_of_week:
                target_days = [int(d.strip()) for d in template.days_of_week.split(',')]
            else:
                target_days = list(range(7))  # All days

            current = start_date
            while current <= end_date:
                if current.weekday() in target_days:
                    dates_to_create.append(current)
                current += timedelta(days=1)

        elif template.frequency == 'monthly':
            day = template.day_of_month or start_date.day
            current = start_date
            while current <= end_date:
                try:
                    target_date = current.replace(day=day)
                    if target_date >= start_date and target_date <= end_date:
                        dates_to_create.append(target_date)
                except ValueError:
                    pass

                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=current.month + 1, day=1)

        # Create tasks for each date
        for task_date in dates_to_create:
            # Check if task already exists
            existing = CalendarTask.objects.filter(
                recurring_template=template,
                scheduled_date=task_date,
                assigned_to=template.assigned_to
            ).exists()

            if not existing:
                CalendarTask.objects.create(
                    family=template.family,
                    assigned_to=template.assigned_to,
                    title=template.chore_title,
                    description=template.chore_description,
                    points=template.points,
                    category=template.category,
                    scheduled_date=task_date,
                    scheduled_time=template.scheduled_time,
                    recurring_template=template,
                    created_by=template.created_by,
                    status=CalendarTask.STATUS_PENDING
                )


# ─── Calendar Views ───────────────────────────────────────────────────────

@login_required
def calendar_view(request):
    """Display the calendar for the user."""
    import calendar as cal_module
    from django.db import models
    user = request.user

    # Get month from query params or use current
    month_str = request.GET.get('month')
    if month_str:
        year, month = map(int, month_str.split('-'))
        current_date = datetime(year, month, 1).date()
    else:
        current_date = timezone.now().date()

    # Get tasks for the month
    first_day = current_date.replace(day=1)
    if current_date.month == 12:
        last_day = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)

    # Auto-generate recurring tasks for this month if they don't exist
    if user.family:
        _generate_recurring_tasks_for_month(user.family, first_day, last_day)

    # Generate all calendar days (including previous and next month days)
    calendar_days = []
    # Get the calendar for the month (0=Monday, 6=Sunday)
    month_calendar = cal_module.monthcalendar(current_date.year, current_date.month)

    # Add days from previous month to fill the first week
    if month_calendar[0][0] != 1:
        prev_month_date = first_day - timedelta(days=1)
        last_day_prev_month = cal_module.monthrange(prev_month_date.year, prev_month_date.month)[1]
        start_day = last_day_prev_month - month_calendar[0][0] + 1
        for day in range(start_day, last_day_prev_month + 1):
            calendar_days.append(prev_month_date.replace(day=day))

    # Add days from current month
    for week in month_calendar:
        for day_num in week:
            if day_num != 0:  # 0 means days from other months
                calendar_days.append(current_date.replace(day=day_num))

    # Add days from next month to fill the last week
    remaining_days = 42 - len(calendar_days)  # 6 weeks * 7 days
    if remaining_days > 0:
        for day in range(1, remaining_days + 1):
            if current_date.month == 12:
                next_month_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                next_month_date = current_date.replace(month=current_date.month + 1)
            calendar_days.append(next_month_date.replace(day=day))

    tasks = CalendarTask.objects.filter(
        family=user.family,
        scheduled_date__range=[first_day, last_day]
    )

    if user.is_child:
        tasks = tasks.filter(assigned_to=user)

    # Group tasks by date
    tasks_by_date = {}
    for task in tasks:
        date_key = task.scheduled_date.isoformat()
        if date_key not in tasks_by_date:
            tasks_by_date[date_key] = []
        tasks_by_date[date_key].append(task)

    prev_month = (current_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    if current_date.month == 12:
        next_month = current_date.replace(year=current_date.year + 1, month=1)
    else:
        next_month = current_date.replace(month=current_date.month + 1)


    # Convert to list of tuples for easier template iteration
    all_tasks_items = list(tasks_by_date.items())

    ctx = {
        'current_date': current_date,
        'calendar_days': calendar_days,
        'tasks_by_date': tasks_by_date,
        'all_tasks_items': all_tasks_items,
        'prev_month': prev_month,
        'next_month': next_month,
        'month_str': f"{current_date.year}-{current_date.month:02d}",
    }
    return render(request, 'calendar_tasks/calendar_view.html', ctx)


@login_required
def calendar_day_detail(request, year, month, day):
    """View tasks for a specific day."""
    user = request.user
    date = datetime(int(year), int(month), int(day)).date()

    tasks = CalendarTask.objects.filter(
        family=user.family,
        scheduled_date=date
    )

    if user.is_child:
        tasks = tasks.filter(assigned_to=user)

    ctx = {
        'date': date,
        'tasks': tasks,
        'is_today': date == timezone.now().date(),
    }
    return render(request, 'calendar_tasks/calendar_day_detail.html', ctx)


@login_required
def task_complete(request, task_id):
    """Kid marks a calendar task as completed."""
    task = get_object_or_404(
        CalendarTask,
        pk=task_id,
        assigned_to=request.user,
        status=CalendarTask.STATUS_PENDING
    )

    if request.method == 'POST':
        form = CalendarTaskCompleteForm(request.POST)
        if form.is_valid():
            task.mark_completed(note=form.cleaned_data.get('note', ''))

            # Send notification to parents
            send_approval_notification.delay(task.id)

            messages.success(request, f"Great job! '{task.title}' submitted for approval! 🌟")
            return redirect('calendar_tasks:calendar_view')
    else:
        form = CalendarTaskCompleteForm()

    return render(request, 'calendar_tasks/task_complete.html', {'task': task, 'form': form})


@login_required
@parent_required
def pending_task_approvals(request):
    """Parent sees all calendar tasks awaiting approval."""
    awaiting = CalendarTask.objects.filter(
        family=request.user.family,
        status=CalendarTask.STATUS_COMPLETED
    ).select_related('assigned_to').order_by('-completed_at')

    ctx = {'awaiting': awaiting}
    return render(request, 'calendar_tasks/pending_task_approvals.html', ctx)


@login_required
@parent_required
def task_approve(request, task_id):
    """Parent approves a calendar task."""
    task = get_object_or_404(
        CalendarTask,
        pk=task_id,
        family=request.user.family,
        status=CalendarTask.STATUS_COMPLETED
    )

    if request.method == 'POST':
        task.approve(approved_by=request.user)
        messages.success(request, f"Approved! {task.assigned_to.display_name} earned {task.points} points! 🎉")
        return redirect('calendar_tasks:pending_task_approvals')

    return render(request, 'calendar_tasks/task_approve.html', {'task': task})


@login_required
@parent_required
def task_reject(request, task_id):
    """Parent rejects a calendar task."""
    task = get_object_or_404(
        CalendarTask,
        pk=task_id,
        family=request.user.family,
        status=CalendarTask.STATUS_COMPLETED
    )

    if request.method == 'POST':
        form = CalendarTaskRejectForm(request.POST)
        if form.is_valid():
            task.reject(
                approved_by=request.user,
                reason=form.cleaned_data.get('reason', '')
            )
            messages.warning(request, f"Task rejected for {task.assigned_to.display_name}.")
            return redirect('calendar_tasks:pending_task_approvals')
    else:
        form = CalendarTaskRejectForm()

    return render(request, 'calendar_tasks/task_reject.html', {'task': task, 'form': form})


# ─── Recurring Chore Management ────────────────────────────────────────────

@login_required
@parent_required
def recurring_templates_list(request):
    """List all recurring chore templates for the family."""
    templates = RecurringChoreTemplate.objects.filter(
        family=request.user.family
    ).select_related('assigned_to', 'created_by')

    ctx = {'templates': templates}
    return render(request, 'calendar_tasks/recurring_templates_list.html', ctx)


@login_required
@parent_required
def create_recurring_template(request):
    """Create a new recurring chore template."""
    if request.method == 'POST':
        form = RecurringChoreTemplateForm(request.user.family, request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.family = request.user.family
            template.created_by = request.user
            template.save()
            messages.success(request, f"Recurring chore '{template.chore_title}' created! 🔄")
            return redirect('calendar_tasks:recurring_templates_list')
    else:
        form = RecurringChoreTemplateForm(request.user.family)

    ctx = {'form': form, 'action': 'Create'}
    return render(request, 'calendar_tasks/recurring_template_form.html', ctx)


@login_required
@parent_required
def edit_recurring_template(request, template_id):
    """Edit a recurring chore template."""
    template = get_object_or_404(
        RecurringChoreTemplate,
        pk=template_id,
        family=request.user.family
    )

    if request.method == 'POST':
        form = RecurringChoreTemplateForm(request.user.family, request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, "Recurring chore updated!")
            return redirect('calendar_tasks:recurring_templates_list')
    else:
        form = RecurringChoreTemplateForm(request.user.family, instance=template)

    ctx = {'form': form, 'action': 'Edit', 'template': template}
    return render(request, 'calendar_tasks/recurring_template_form.html', ctx)


@login_required
@parent_required
def delete_recurring_template(request, template_id):
    """Deactivate a recurring chore template."""
    template = get_object_or_404(
        RecurringChoreTemplate,
        pk=template_id,
        family=request.user.family
    )

    if request.method == 'POST':
        template.is_active = False
        template.save()
        messages.success(request, f"Recurring chore '{template.chore_title}' deactivated.")
        return redirect('calendar_tasks:recurring_templates_list')

    return render(request, 'calendar_tasks/recurring_template_confirm_delete.html', {'template': template})


# ─── Manual Calendar Task Management ────────────────────────────────────────

@login_required
@parent_required
def create_calendar_task(request):
    """Parent creates a manual calendar task for one or more children."""
    child = None

    if request.method == 'POST':
        form = CalendarTaskForm(request.user.family, request.POST)
        if form.is_valid():
            # Get children - support both single and multiple
            assigned_children = form.cleaned_data.get('assigned_to_multiple', [])
            
            # Fallback to single child from GET or POST
            if not assigned_children:
                child_id = request.GET.get('child') or request.POST.get('assigned_to')
                if child_id:
                    try:
                        assigned_children = [User.objects.get(pk=child_id, family=request.user.family, role=User.ROLE_CHILD)]
                    except User.DoesNotExist:
                        messages.error(request, "Invalid child selected.")
                        return redirect('calendar_tasks:calendar_view')
            
            if not assigned_children:
                messages.error(request, "Please select at least one child to assign this task to.")
                return redirect('calendar_tasks:calendar_view')

            task = form.save(commit=False)
            task.family = request.user.family
            task.assigned_to = assigned_children[0]  # Primary assignment for backward compatibility
            task.created_by = request.user
            task.save()
            
            # Create assignments for all selected children
            from .models import CalendarTaskAssignment
            for child_user in assigned_children:
                CalendarTaskAssignment.objects.create(
                    task=task,
                    assigned_to=child_user
                )
            
            children_names = ', '.join([c.display_name for c in assigned_children])
            messages.success(request, f"Task '{task.title}' created for {children_names}! 📋")
            return redirect('calendar_tasks:calendar_view')
    else:
        form = CalendarTaskForm(request.user.family)
        child_id = request.GET.get('child')
        if child_id:
            try:
                child = User.objects.get(pk=child_id, family=request.user.family, role=User.ROLE_CHILD)
            except User.DoesNotExist:
                child = None

    ctx = {'form': form, 'child': child}
    return render(request, 'calendar_tasks/create_calendar_task.html', ctx)


@login_required
@parent_required
def edit_calendar_task(request, task_id):
    """Edit a calendar task."""
    task = get_object_or_404(
        CalendarTask,
        pk=task_id,
        family=request.user.family
    )

    if request.method == 'POST':
        form = CalendarTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated!")
            return redirect('calendar_tasks:calendar_view')
    else:
        form = CalendarTaskForm(instance=task)

    ctx = {'form': form, 'task': task}
    return render(request, 'calendar_tasks/create_calendar_task.html', ctx)


@login_required
@parent_required
def delete_calendar_task(request, task_id):
    """Delete a calendar task."""
    task = get_object_or_404(
        CalendarTask,
        pk=task_id,
        family=request.user.family,
        status=CalendarTask.STATUS_PENDING
    )

    if request.method == 'POST':
        task.delete()
        messages.success(request, "Task deleted.")
        return redirect('calendar_tasks:calendar_view')

    return render(request, 'calendar_tasks/delete_calendar_task.html', {'task': task})


# ─── Schedule Patterns (Holidays, Breaks) ──────────────────────────────────

@login_required
@parent_required
def schedule_patterns_list(request):
    """List all schedule patterns."""
    patterns = SchedulePattern.objects.filter(
        family=request.user.family
    ).order_by('start_date')

    ctx = {'patterns': patterns}
    return render(request, 'calendar_tasks/schedule_patterns_list.html', ctx)


@login_required
@parent_required
def create_schedule_pattern(request):
    """Create a schedule pattern (holiday, break, etc.)."""
    if request.method == 'POST':
        form = SchedulePatternForm(request.POST)
        if form.is_valid():
            pattern = form.save(commit=False)
            pattern.family = request.user.family
            pattern.save()
            messages.success(request, f"Schedule pattern '{pattern.name}' created! 📅")
            return redirect('calendar_tasks:schedule_patterns_list')
    else:
        form = SchedulePatternForm()

    ctx = {'form': form, 'action': 'Create'}
    return render(request, 'calendar_tasks/schedule_pattern_form.html', ctx)


@login_required
@parent_required
def edit_schedule_pattern(request, pattern_id):
    """Edit a schedule pattern."""
    pattern = get_object_or_404(
        SchedulePattern,
        pk=pattern_id,
        family=request.user.family
    )

    if request.method == 'POST':
        form = SchedulePatternForm(request.POST, instance=pattern)
        if form.is_valid():
            form.save()
            messages.success(request, "Pattern updated!")
            return redirect('calendar_tasks:schedule_patterns_list')
    else:
        form = SchedulePatternForm(instance=pattern)

    ctx = {'form': form, 'pattern': pattern}
    return render(request, 'calendar_tasks/schedule_pattern_form.html', ctx)


@login_required
@parent_required
def delete_schedule_pattern(request, pattern_id):
    """Delete a schedule pattern."""
    pattern = get_object_or_404(
        SchedulePattern,
        pk=pattern_id,
        family=request.user.family
    )

    if request.method == 'POST':
        pattern.delete()
        messages.success(request, "Pattern deleted.")
        return redirect('calendar_tasks:schedule_patterns_list')

    return render(request, 'calendar_tasks/schedule_pattern_confirm_delete.html', {'pattern': pattern})


# ─── Bad Deeds Management ──────────────────────────────────────────────────

@login_required
@parent_required
def bad_deeds_list(request):
    """List all bad deeds for the family."""
    bad_deeds = BadDeed.objects.filter(
        family=request.user.family
    ).select_related('assigned_to', 'created_by')

    ctx = {'bad_deeds': bad_deeds}
    return render(request, 'calendar_tasks/bad_deeds_list.html', ctx)


@login_required
@parent_required
def create_bad_deed(request):
    """Create a recurring bad deed template."""
    if request.method == 'POST':
        form = BadDeedForm(request.user.family, request.POST)
        if form.is_valid():
            bad_deed = form.save(commit=False)
            bad_deed.family = request.user.family
            bad_deed.created_by = request.user
            bad_deed.save()
            messages.success(request, f"Bad deed '{bad_deed.title}' created! ⚠️")
            return redirect('calendar_tasks:bad_deeds_list')
    else:
        form = BadDeedForm(request.user.family)

    ctx = {'form': form, 'action': 'Create'}
    return render(request, 'calendar_tasks/bad_deed_form.html', ctx)


@login_required
@parent_required
def edit_bad_deed(request, bad_deed_id):
    """Edit a bad deed template."""
    bad_deed = get_object_or_404(
        BadDeed,
        pk=bad_deed_id,
        family=request.user.family
    )

    if request.method == 'POST':
        form = BadDeedForm(request.user.family, request.POST, instance=bad_deed)
        if form.is_valid():
            form.save()
            messages.success(request, "Bad deed updated!")
            return redirect('calendar_tasks:bad_deeds_list')
    else:
        form = BadDeedForm(request.user.family, instance=bad_deed)

    ctx = {'form': form, 'action': 'Edit', 'bad_deed': bad_deed}
    return render(request, 'calendar_tasks/bad_deed_form.html', ctx)


@login_required
@parent_required
def delete_bad_deed(request, bad_deed_id):
    """Deactivate a bad deed template."""
    bad_deed = get_object_or_404(
        BadDeed,
        pk=bad_deed_id,
        family=request.user.family
    )

    if request.method == 'POST':
        bad_deed.is_active = False
        bad_deed.save()
        messages.success(request, f"Bad deed '{bad_deed.title}' deactivated.")
        return redirect('calendar_tasks:bad_deeds_list')

    return render(request, 'calendar_tasks/bad_deed_confirm_delete.html', {'bad_deed': bad_deed})


@login_required
@parent_required
def add_bad_deed_instance(request, child_id=None):
    """Parent adds a one-time bad deed instance (direct point deduction)."""
    child = None
    if child_id:
        child = get_object_or_404(User, pk=child_id, family=request.user.family, role=User.ROLE_CHILD)

    if request.method == 'POST':
        form = BadDeedInstanceForm(request.POST)
        if form.is_valid():
            # Get child from POST if not in URL
            child_id = request.POST.get('assigned_to')
            if not child_id:
                messages.error(request, "Please select a child.")
                return redirect('calendar_tasks:add_bad_deed_instance')

            child = get_object_or_404(User, pk=child_id, family=request.user.family, role=User.ROLE_CHILD)

            # Create bad deed instance
            instance = form.save(commit=False)
            instance.family = request.user.family
            instance.assigned_to = child
            instance.created_by = request.user
            instance.status = BadDeedInstance.STATUS_ACTIVE
            instance.save()

            # IMMEDIATELY deduct points (no approval needed)
            child.add_points(
                instance.negative_points,
                reason=f"Bad deed: {instance.title} ({instance.reason})",
                added_by=request.user
            )

            messages.success(
                request,
                f"⚠️ {child.display_name} has been deducted {abs(instance.negative_points)} points for: {instance.title}"
            )
            return redirect('calendar_tasks:bad_deeds_instances')
    else:
        form = BadDeedInstanceForm()

    ctx = {'form': form, 'child': child}
    return render(request, 'calendar_tasks/add_bad_deed_instance.html', ctx)


@login_required
@parent_required
def bad_deeds_instances(request):
    """View all bad deed instances (deductions made)."""
    instances = BadDeedInstance.objects.filter(
        family=request.user.family
    ).select_related('assigned_to', 'created_by', 'removed_by').order_by('-created_at')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        instances = instances.filter(status=status_filter)

    # Filter by child
    child_id = request.GET.get('child')
    if child_id:
        instances = instances.filter(assigned_to_id=child_id)

    ctx = {
        'instances': instances,
        'children': User.objects.filter(family=request.user.family, role=User.ROLE_CHILD)
    }
    return render(request, 'calendar_tasks/bad_deeds_instances.html', ctx)


@login_required
@parent_required
def remove_bad_deed(request, instance_id):
    """Remove/reverse a bad deed (restore points)."""
    instance = get_object_or_404(
        BadDeedInstance,
        pk=instance_id,
        family=request.user.family,
        status=BadDeedInstance.STATUS_ACTIVE
    )

    if request.method == 'POST':
        # Restore points
        instance.assigned_to.add_points(
            abs(instance.negative_points),
            reason=f"Bad deed reversed: {instance.title}",
            added_by=request.user
        )

        # Mark as removed
        instance.status = BadDeedInstance.STATUS_REMOVED
        instance.removed_by = request.user
        instance.removed_at = timezone.now()
        instance.save()

        messages.success(
            request,
            f"✅ {instance.assigned_to.display_name} has been restored {abs(instance.negative_points)} points."
        )
        return redirect('calendar_tasks:bad_deeds_instances')

    return render(request, 'calendar_tasks/remove_bad_deed_confirm.html', {'instance': instance})

