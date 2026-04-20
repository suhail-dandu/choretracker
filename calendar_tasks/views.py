from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import CalendarTask, RecurringChoreTemplate, SchedulePattern, BadDeed, BadDeedInstance, CalendarTaskAssignment
from .forms import (
    CalendarTaskForm, CalendarTaskCompleteForm, CalendarTaskRejectForm,
    RecurringChoreTemplateForm, SchedulePatternForm, BadDeedForm, BadDeedInstanceForm
)
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
    from django.db import models as db_models

    templates = RecurringChoreTemplate.objects.filter(
        family=family,
        is_active=True,
        start_date__lte=end_date
    ).filter(
        db_models.Q(end_date__isnull=True) | db_models.Q(end_date__gte=start_date)
    )

    for template in templates:
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
                target_days = list(range(7))

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
                    if start_date <= target_date <= end_date:
                        dates_to_create.append(target_date)
                except ValueError:
                    pass

                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=current.month + 1, day=1)

        for task_date in dates_to_create:
            existing_task = CalendarTask.objects.filter(
                recurring_template=template,
                scheduled_date=task_date,
                assigned_to=template.assigned_to
            ).first()

            if not existing_task:
                existing_task = CalendarTask.objects.create(
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
            # Ensure the assignment exists (handles both new and pre-existing tasks)
            CalendarTaskAssignment.objects.get_or_create(
                task=existing_task,
                assigned_to=template.assigned_to
            )


# ─── Calendar Views ───────────────────────────────────────────────────────

@login_required
def calendar_view(request):
    """Display the calendar for the user."""
    import calendar as cal_module
    user = request.user

    month_str = request.GET.get('month')
    if month_str:
        year, month = map(int, month_str.split('-'))
        current_date = datetime(year, month, 1).date()
    else:
        current_date = timezone.now().date()

    first_day = current_date.replace(day=1)
    if current_date.month == 12:
        last_day = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)

    if user.family:
        _generate_recurring_tasks_for_month(user.family, first_day, last_day)

    # Build calendar day grid
    calendar_days = []
    month_calendar = cal_module.monthcalendar(current_date.year, current_date.month)

    if month_calendar[0][0] != 1:
        prev_month_date = first_day - timedelta(days=1)
        last_day_prev_month = cal_module.monthrange(prev_month_date.year, prev_month_date.month)[1]
        start_day = last_day_prev_month - month_calendar[0][0] + 1
        for day in range(start_day, last_day_prev_month + 1):
            calendar_days.append(prev_month_date.replace(day=day))

    for week in month_calendar:
        for day_num in week:
            if day_num != 0:
                calendar_days.append(current_date.replace(day=day_num))

    remaining_days = 42 - len(calendar_days)
    if remaining_days > 0:
        if current_date.month == 12:
            next_month_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            next_month_date = current_date.replace(month=current_date.month + 1)
        for day in range(1, remaining_days + 1):
            calendar_days.append(next_month_date.replace(day=day))

    if user.is_child:
        # Build map from existing CalendarTaskAssignment records
        kid_assignments = {
            ka.task_id: ka
            for ka in CalendarTaskAssignment.objects.filter(
                assigned_to=user,
                task__family=user.family,
                task__scheduled_date__range=[first_day, last_day]
            ).select_related('task')
        }

        # Also pick up tasks directly assigned to this kid that have no assignment record yet
        direct_tasks = CalendarTask.objects.filter(
            family=user.family,
            assigned_to=user,
            scheduled_date__range=[first_day, last_day]
        ).exclude(id__in=kid_assignments.keys())

        for task in direct_tasks:
            assignment, _ = CalendarTaskAssignment.objects.get_or_create(
                task=task, assigned_to=user
            )
            kid_assignments[task.id] = assignment

        tasks = list(CalendarTask.objects.filter(id__in=kid_assignments.keys()))
        # Annotate each task with this child's specific status
        for task in tasks:
            task.display_status = kid_assignments[task.id].status
    else:
        tasks = list(CalendarTask.objects.filter(
            family=user.family,
            scheduled_date__range=[first_day, last_day]
        ))
        for task in tasks:
            task.display_status = task.status

    tasks_by_date = {}
    for task in tasks:
        date_key = task.scheduled_date.isoformat()
        if date_key not in tasks_by_date:
            tasks_by_date[date_key] = []
        tasks_by_date[date_key].append(task)

    prev_month = (first_day - timedelta(days=1)).replace(day=1)
    if current_date.month == 12:
        next_month = current_date.replace(year=current_date.year + 1, month=1)
    else:
        next_month = current_date.replace(month=current_date.month + 1)

    ctx = {
        'current_date': current_date,
        'calendar_days': calendar_days,
        'tasks_by_date': tasks_by_date,
        'all_tasks_items': list(tasks_by_date.items()),
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

    if user.is_child:
        # Build assignment map (existing records)
        existing_map = {
            ka.task_id: ka
            for ka in CalendarTaskAssignment.objects.filter(
                assigned_to=user,
                task__family=user.family,
                task__scheduled_date=date
            ).select_related('task')
        }

        # Also pick up tasks directly assigned to this kid with no assignment record
        direct_tasks = CalendarTask.objects.filter(
            family=user.family,
            assigned_to=user,
            scheduled_date=date
        ).exclude(id__in=existing_map.keys())

        for task in direct_tasks:
            assignment, _ = CalendarTaskAssignment.objects.get_or_create(
                task=task, assigned_to=user
            )
            existing_map[task.id] = assignment

        # Re-query to get properly ordered assignments with all fields
        assignments = CalendarTaskAssignment.objects.filter(
            assigned_to=user,
            task_id__in=existing_map.keys()
        ).select_related('task').order_by('task__scheduled_time')

        ctx = {
            'date': date,
            'assignments': assignments,
            'is_today': date == timezone.now().date(),
        }
    else:
        # For parents: show all family tasks with assigned children info
        tasks = CalendarTask.objects.filter(
            family=user.family,
            scheduled_date=date
        ).prefetch_related('child_assignments__assigned_to').order_by('scheduled_time')

        ctx = {
            'date': date,
            'tasks': tasks,
            'is_today': date == timezone.now().date(),
        }

    return render(request, 'calendar_tasks/calendar_day_detail.html', ctx)


@login_required
def task_complete(request, task_id):
    """Kid marks a calendar task as completed."""
    # Verify the task belongs to this kid's family
    task = get_object_or_404(CalendarTask, pk=task_id, family=request.user.family)

    # Always get or create the CalendarTaskAssignment — this ensures the parent
    # approval queue (which only queries CalendarTaskAssignment) always sees it.
    assignment, _ = CalendarTaskAssignment.objects.get_or_create(
        task=task,
        assigned_to=request.user
    )

    # If already processed, don't show the form again
    if assignment.status != CalendarTaskAssignment.STATUS_PENDING:
        messages.info(request, f"'{task.title}' has already been submitted or approved.")
        return redirect('calendar_tasks:calendar_view')

    if request.method == 'POST':
        form = CalendarTaskCompleteForm(request.POST)
        if form.is_valid():
            note = form.cleaned_data.get('note', '')

            # Mark the assignment completed — this is what parents query for approvals
            assignment.mark_completed(note=note)

            # Also sync the linked ChoreAssignment if present
            if assignment.chore_assignment and assignment.chore_assignment.status == 'pending':
                ca = assignment.chore_assignment
                ca.status = 'completed'
                ca.completed_at = timezone.now()
                ca.note = note
                ca.save(update_fields=['status', 'completed_at', 'note'])

            try:
                from .tasks import send_approval_notification
                send_approval_notification.delay(task.id)
            except Exception:
                pass

            messages.success(request, f"Great job! '{task.title}' submitted for approval! 🌟")
            return redirect('calendar_tasks:calendar_view')
    else:
        form = CalendarTaskCompleteForm()

    return render(request, 'calendar_tasks/task_complete.html', {'task': task, 'form': form})


@login_required
@parent_required
def pending_task_approvals(request):
    """Parent sees all calendar task assignments awaiting approval."""
    awaiting_assignments = CalendarTaskAssignment.objects.filter(
        task__family=request.user.family,
        status=CalendarTaskAssignment.STATUS_COMPLETED
    ).select_related('task', 'assigned_to').order_by('-completed_at')

    ctx = {
        'awaiting_assignments': awaiting_assignments,
    }
    return render(request, 'calendar_tasks/pending_task_approvals.html', ctx)


@login_required
@parent_required
def assignment_approve(request, assignment_id):
    """Parent approves a single child's task completion."""
    assignment = get_object_or_404(
        CalendarTaskAssignment,
        pk=assignment_id,
        task__family=request.user.family,
        status=CalendarTaskAssignment.STATUS_COMPLETED
    )

    if request.method == 'POST':
        chore_assign = assignment.chore_assignment
        if chore_assign and chore_assign.status == 'completed':
            # Kid completed via chore route — ChoreAssignment.approve() handles points + badges + sync
            chore_assign.approve(approved_by=request.user)
        else:
            # Kid completed via calendar route — approve CalendarTaskAssignment directly
            assignment.approve(approved_by=request.user)
            # Sync linked ChoreAssignment to approved if present
            if chore_assign and chore_assign.status not in ('approved', 'rejected'):
                chore_assign.status = 'approved'
                chore_assign.approved_by = request.user
                chore_assign.approved_at = timezone.now()
                chore_assign.points_awarded = assignment.task.points
                chore_assign.save(update_fields=['status', 'approved_by', 'approved_at', 'points_awarded'])

        messages.success(request, f"Approved! {assignment.assigned_to.display_name} earned {assignment.task.points} points! 🎉")
        return redirect('calendar_tasks:pending_task_approvals')

    return render(request, 'calendar_tasks/assignment_approve.html', {'assignment': assignment})


@login_required
@parent_required
def assignment_reject(request, assignment_id):
    """Parent rejects a single child's task completion."""
    assignment = get_object_or_404(
        CalendarTaskAssignment,
        pk=assignment_id,
        task__family=request.user.family,
        status=CalendarTaskAssignment.STATUS_COMPLETED
    )

    if request.method == 'POST':
        form = CalendarTaskRejectForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data.get('reason', '')
            chore_assign = assignment.chore_assignment

            if chore_assign and chore_assign.status == 'completed':
                chore_assign.reject(approved_by=request.user, reason=reason)
            else:
                assignment.reject(approved_by=request.user, reason=reason)
                if chore_assign and chore_assign.status not in ('approved', 'rejected'):
                    chore_assign.status = 'rejected'
                    chore_assign.approved_by = request.user
                    chore_assign.rejection_reason = reason
                    chore_assign.save(update_fields=['status', 'approved_by', 'rejection_reason'])

            messages.warning(request, f"Task rejected for {assignment.assigned_to.display_name}.")
            return redirect('calendar_tasks:pending_task_approvals')
    else:
        form = CalendarTaskRejectForm()

    return render(request, 'calendar_tasks/assignment_reject.html', {'assignment': assignment, 'form': form})


@login_required
@parent_required
def task_approve(request, task_id):
    """Parent approves a calendar task (legacy: tasks without per-child assignments)."""
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
    """Parent rejects a calendar task (legacy)."""
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
    templates = RecurringChoreTemplate.objects.filter(
        family=request.user.family
    ).select_related('assigned_to', 'created_by')

    return render(request, 'calendar_tasks/recurring_templates_list.html', {'templates': templates})


@login_required
@parent_required
def create_recurring_template(request):
    if request.method == 'POST':
        form = RecurringChoreTemplateForm(request.user.family, request.POST)
        if form.is_valid():
            assigned_children = list(form.cleaned_data.get('assigned_to_multiple', []))
            if not assigned_children:
                assigned_to = form.cleaned_data.get('assigned_to')
                if assigned_to:
                    assigned_children = [assigned_to]

            if not assigned_children:
                messages.error(request, "Please select at least one child.")
                return redirect('calendar_tasks:create_recurring_template')

            for child in assigned_children:
                RecurringChoreTemplate.objects.create(
                    family=request.user.family,
                    chore_title=form.cleaned_data['chore_title'],
                    chore_description=form.cleaned_data.get('chore_description', ''),
                    points=form.cleaned_data['points'],
                    category=form.cleaned_data.get('category', 'other'),
                    frequency=form.cleaned_data.get('frequency', 'weekly'),
                    days_of_week=form.cleaned_data.get('days_of_week', ''),
                    day_of_month=form.cleaned_data.get('day_of_month'),
                    assigned_to=child,
                    scheduled_time=form.cleaned_data.get('scheduled_time'),
                    start_date=form.cleaned_data.get('start_date'),
                    end_date=form.cleaned_data.get('end_date'),
                    created_by=request.user
                )

            children_names = ', '.join([c.display_name for c in assigned_children])
            messages.success(request, f"Recurring chore '{form.cleaned_data['chore_title']}' created for {children_names}! 🔄")
            return redirect('calendar_tasks:recurring_templates_list')
    else:
        form = RecurringChoreTemplateForm(request.user.family)

    return render(request, 'calendar_tasks/recurring_template_form.html', {'form': form, 'action': 'Create'})


@login_required
@parent_required
def edit_recurring_template(request, template_id):
    template = get_object_or_404(RecurringChoreTemplate, pk=template_id, family=request.user.family)

    if request.method == 'POST':
        form = RecurringChoreTemplateForm(request.user.family, request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, "Recurring chore updated!")
            return redirect('calendar_tasks:recurring_templates_list')
    else:
        form = RecurringChoreTemplateForm(request.user.family, instance=template)

    return render(request, 'calendar_tasks/recurring_template_form.html', {'form': form, 'action': 'Edit', 'template': template})


@login_required
@parent_required
def delete_recurring_template(request, template_id):
    template = get_object_or_404(RecurringChoreTemplate, pk=template_id, family=request.user.family)

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
            assigned_children = list(form.cleaned_data.get('assigned_to_multiple', []))

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
            task.assigned_to = assigned_children[0]
            task.created_by = request.user
            task.save()

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

    return render(request, 'calendar_tasks/create_calendar_task.html', {'form': form, 'child': child})


@login_required
@parent_required
def edit_calendar_task(request, task_id):
    task = get_object_or_404(CalendarTask, pk=task_id, family=request.user.family)

    if request.method == 'POST':
        form = CalendarTaskForm(request.user.family, request.POST, instance=task)
        if form.is_valid():
            form.save()

            assigned_children = list(form.cleaned_data.get('assigned_to_multiple', []))
            if assigned_children:
                CalendarTaskAssignment.objects.filter(task=task).delete()
                for child in assigned_children:
                    CalendarTaskAssignment.objects.get_or_create(task=task, assigned_to=child)

            messages.success(request, "Task updated!")
            return redirect('calendar_tasks:calendar_view')
    else:
        form = CalendarTaskForm(request.user.family, instance=task)

    return render(request, 'calendar_tasks/create_calendar_task.html', {'form': form, 'task': task})


@login_required
@parent_required
def delete_calendar_task(request, task_id):
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
    patterns = SchedulePattern.objects.filter(family=request.user.family).order_by('start_date')
    return render(request, 'calendar_tasks/schedule_patterns_list.html', {'patterns': patterns})


@login_required
@parent_required
def create_schedule_pattern(request):
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

    return render(request, 'calendar_tasks/schedule_pattern_form.html', {'form': form, 'action': 'Create'})


@login_required
@parent_required
def edit_schedule_pattern(request, pattern_id):
    pattern = get_object_or_404(SchedulePattern, pk=pattern_id, family=request.user.family)

    if request.method == 'POST':
        form = SchedulePatternForm(request.POST, instance=pattern)
        if form.is_valid():
            form.save()
            messages.success(request, "Pattern updated!")
            return redirect('calendar_tasks:schedule_patterns_list')
    else:
        form = SchedulePatternForm(instance=pattern)

    return render(request, 'calendar_tasks/schedule_pattern_form.html', {'form': form, 'pattern': pattern})


@login_required
@parent_required
def delete_schedule_pattern(request, pattern_id):
    pattern = get_object_or_404(SchedulePattern, pk=pattern_id, family=request.user.family)

    if request.method == 'POST':
        pattern.delete()
        messages.success(request, "Pattern deleted.")
        return redirect('calendar_tasks:schedule_patterns_list')

    return render(request, 'calendar_tasks/schedule_pattern_confirm_delete.html', {'pattern': pattern})


# ─── Bad Deeds Management ──────────────────────────────────────────────────

@login_required
@parent_required
def bad_deeds_list(request):
    bad_deeds = BadDeed.objects.filter(
        family=request.user.family
    ).select_related('assigned_to', 'created_by')
    return render(request, 'calendar_tasks/bad_deeds_list.html', {'bad_deeds': bad_deeds})


@login_required
@parent_required
def create_bad_deed(request):
    if request.method == 'POST':
        form = BadDeedForm(request.user.family, request.POST)
        if form.is_valid():
            assigned_children = list(form.cleaned_data.get('assigned_to_multiple', []))
            if not assigned_children:
                assigned_to = form.cleaned_data.get('assigned_to')
                if assigned_to:
                    assigned_children = [assigned_to]

            if not assigned_children:
                messages.error(request, "Please select at least one child.")
                return redirect('calendar_tasks:create_bad_deed')

            for child in assigned_children:
                bad_deed = BadDeed.objects.create(
                    family=request.user.family,
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data.get('description', ''),
                    negative_points=form.cleaned_data['negative_points'],
                    category=form.cleaned_data.get('category', 'other'),
                    is_recurring=form.cleaned_data.get('is_recurring', False),
                    frequency=form.cleaned_data.get('frequency', 'weekly'),
                    days_of_week=form.cleaned_data.get('days_of_week', ''),
                    day_of_month=form.cleaned_data.get('day_of_month'),
                    assigned_to=child,
                    scheduled_time=form.cleaned_data.get('scheduled_time'),
                    start_date=form.cleaned_data.get('start_date'),
                    end_date=form.cleaned_data.get('end_date'),
                    created_by=request.user
                )
                if bad_deed.is_recurring:
                    bad_deed.generate_calendar_entries()

            children_names = ', '.join([c.display_name for c in assigned_children])
            messages.success(request, f"Bad deed '{form.cleaned_data['title']}' created for {children_names}! ⚠️")
            return redirect('calendar_tasks:bad_deeds_list')
    else:
        form = BadDeedForm(request.user.family)

    return render(request, 'calendar_tasks/bad_deed_form.html', {'form': form, 'action': 'Create'})


@login_required
@parent_required
def edit_bad_deed(request, bad_deed_id):
    bad_deed = get_object_or_404(BadDeed, pk=bad_deed_id, family=request.user.family)

    if request.method == 'POST':
        form = BadDeedForm(request.user.family, request.POST, instance=bad_deed)
        if form.is_valid():
            form.save()
            messages.success(request, "Bad deed updated!")
            return redirect('calendar_tasks:bad_deeds_list')
    else:
        form = BadDeedForm(request.user.family, instance=bad_deed)

    return render(request, 'calendar_tasks/bad_deed_form.html', {'form': form, 'action': 'Edit', 'bad_deed': bad_deed})


@login_required
@parent_required
def delete_bad_deed(request, bad_deed_id):
    bad_deed = get_object_or_404(BadDeed, pk=bad_deed_id, family=request.user.family)

    if request.method == 'POST':
        bad_deed.is_active = False
        bad_deed.save()
        messages.success(request, f"Bad deed '{bad_deed.title}' deactivated.")
        return redirect('calendar_tasks:bad_deeds_list')

    return render(request, 'calendar_tasks/bad_deed_confirm_delete.html', {'bad_deed': bad_deed})


@login_required
@parent_required
def add_bad_deed_instance(request, child_id=None):
    child = None
    if child_id:
        child = get_object_or_404(User, pk=child_id, family=request.user.family, role=User.ROLE_CHILD)

    if request.method == 'POST':
        form = BadDeedInstanceForm(request.POST)
        if form.is_valid():
            child_id = request.POST.get('assigned_to')
            if not child_id:
                messages.error(request, "Please select a child.")
                return redirect('calendar_tasks:add_bad_deed_instance')

            child = get_object_or_404(User, pk=child_id, family=request.user.family, role=User.ROLE_CHILD)

            instance = form.save(commit=False)
            instance.family = request.user.family
            instance.assigned_to = child
            instance.created_by = request.user
            instance.status = BadDeedInstance.STATUS_ACTIVE
            instance.save()

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

    return render(request, 'calendar_tasks/add_bad_deed_instance.html', {'form': form, 'child': child})


@login_required
@parent_required
def bad_deeds_instances(request):
    instances = BadDeedInstance.objects.filter(
        family=request.user.family
    ).select_related('assigned_to', 'created_by', 'removed_by').order_by('-created_at')

    status_filter = request.GET.get('status')
    if status_filter:
        instances = instances.filter(status=status_filter)

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
    instance = get_object_or_404(
        BadDeedInstance,
        pk=instance_id,
        family=request.user.family,
        status=BadDeedInstance.STATUS_ACTIVE
    )

    if request.method == 'POST':
        instance.assigned_to.add_points(
            abs(instance.negative_points),
            reason=f"Bad deed reversed: {instance.title}",
            added_by=request.user
        )

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
