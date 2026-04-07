import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from .models import Chore, ChoreAssignment, PointTransaction, PocketMoneyPayout
from .forms import ChoreForm, AssignChoreForm, CompleteChoreForm, RejectChoreForm, PayoutForm
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


# ─── Chore CRUD ───────────────────────────────────────────────────────────────

@login_required
@parent_required
def chore_list(request):
    chores = Chore.objects.filter(family=request.user.family, is_active=True)
    return render(request, 'chores/chore_list.html', {'chores': chores})


@login_required
@parent_required
def chore_create(request):
    if request.method == 'POST':
        form = ChoreForm(request.POST)
        if form.is_valid():
            chore = form.save(commit=False)
            chore.family = request.user.family
            chore.created_by = request.user
            chore.save()
            messages.success(request, f"Chore '{chore.title}' created! 🎉")
            return redirect('chores:assign', chore_id=chore.pk)
    else:
        form = ChoreForm()
    return render(request, 'chores/chore_form.html', {'form': form, 'action': 'Create'})


@login_required
@parent_required
def chore_edit(request, chore_id):
    chore = get_object_or_404(Chore, pk=chore_id, family=request.user.family)
    if request.method == 'POST':
        form = ChoreForm(request.POST, instance=chore)
        if form.is_valid():
            form.save()
            messages.success(request, "Chore updated!")
            return redirect('chores:list')
    else:
        form = ChoreForm(instance=chore)
    return render(request, 'chores/chore_form.html', {'form': form, 'chore': chore, 'action': 'Edit'})


@login_required
@parent_required
def chore_delete(request, chore_id):
    chore = get_object_or_404(Chore, pk=chore_id, family=request.user.family)
    if request.method == 'POST':
        chore.is_active = False
        chore.save()
        messages.success(request, f"Chore '{chore.title}' removed.")
        return redirect('chores:list')
    return render(request, 'chores/chore_confirm_delete.html', {'chore': chore})


# ─── Assignment workflow ───────────────────────────────────────────────────────

@login_required
@parent_required
def assign_chore(request, chore_id):
    chore = get_object_or_404(Chore, pk=chore_id, family=request.user.family)
    if request.method == 'POST':
        form = AssignChoreForm(request.user.family, request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.chore = chore
            assignment.assigned_by = request.user
            assignment.save()
            kid = assignment.assigned_to
            messages.success(request, f"Assigned '{chore.title}' to {kid.display_name}! 📋")
            return redirect('dashboard:home')
    else:
        form = AssignChoreForm(request.user.family)
    return render(request, 'chores/assign_chore.html', {'form': form, 'chore': chore})


@login_required
def my_chores(request):
    """Kid views their own assignments."""
    assignments = ChoreAssignment.objects.filter(
        assigned_to=request.user
    ).select_related('chore')
    pending = assignments.filter(status=ChoreAssignment.STATUS_PENDING)
    awaiting = assignments.filter(status=ChoreAssignment.STATUS_COMPLETED)
    approved = assignments.filter(status=ChoreAssignment.STATUS_APPROVED)[:10]
    rejected = assignments.filter(status=ChoreAssignment.STATUS_REJECTED)[:5]
    return render(request, 'chores/my_chores.html', {
        'pending': pending,
        'awaiting': awaiting,
        'approved': approved,
        'rejected': rejected,
    })


@login_required
def complete_chore(request, assignment_id):
    """Kid marks a chore as completed."""
    assignment = get_object_or_404(
        ChoreAssignment, pk=assignment_id,
        assigned_to=request.user, status=ChoreAssignment.STATUS_PENDING
    )
    if request.method == 'POST':
        form = CompleteChoreForm(request.POST)
        if form.is_valid():
            assignment.mark_completed(note=form.cleaned_data.get('note', ''))
            messages.success(request, f"Great job! '{assignment.chore.title}' submitted for approval! 🌟")
            return redirect('chores:my_chores')
    else:
        form = CompleteChoreForm()
    return render(request, 'chores/complete_chore.html', {'assignment': assignment, 'form': form})


@login_required
@parent_required
def pending_approvals(request):
    """Parent sees all tasks awaiting approval."""
    awaiting = ChoreAssignment.objects.filter(
        chore__family=request.user.family,
        status=ChoreAssignment.STATUS_COMPLETED
    ).select_related('chore', 'assigned_to')
    return render(request, 'chores/pending_approvals.html', {'awaiting': awaiting})


@login_required
@parent_required
def approve_chore(request, assignment_id):
    assignment = get_object_or_404(
        ChoreAssignment, pk=assignment_id,
        chore__family=request.user.family,
        status=ChoreAssignment.STATUS_COMPLETED
    )
    if request.method == 'POST':
        assignment.approve(approved_by=request.user)
        pts = assignment.chore.points
        kid = assignment.assigned_to
        messages.success(request, f"Approved! {kid.display_name} earned {pts} points! 🎉")
        return redirect('chores:pending_approvals')
    return render(request, 'chores/approve_chore.html', {'assignment': assignment})


@login_required
@parent_required
def reject_chore(request, assignment_id):
    assignment = get_object_or_404(
        ChoreAssignment, pk=assignment_id,
        chore__family=request.user.family,
        status=ChoreAssignment.STATUS_COMPLETED
    )
    if request.method == 'POST':
        form = RejectChoreForm(request.POST)
        if form.is_valid():
            assignment.reject(
                approved_by=request.user,
                reason=form.cleaned_data.get('reason', '')
            )
            messages.warning(request, f"Chore rejected for {assignment.assigned_to.display_name}.")
            return redirect('chores:pending_approvals')
    else:
        form = RejectChoreForm()
    return render(request, 'chores/reject_chore.html', {'assignment': assignment, 'form': form})


# ─── Pocket Money Payout ──────────────────────────────────────────────────────

@login_required
@parent_required
def payout(request, kid_id):
    """Pay out pocket money and reset points."""
    kid = get_object_or_404(User, pk=kid_id, family=request.user.family, role=User.ROLE_CHILD)
    family = request.user.family
    amount_euros = round(kid.total_points / family.points_per_unit, 2)

    if request.method == 'POST':
        form = PayoutForm(request.POST)
        if form.is_valid():
            if kid.total_points <= 0:
                messages.error(request, f"{kid.display_name} has no points to pay out.")
                return redirect('accounts:kid_profile', kid_id=kid.pk)

            month = timezone.now().strftime('%Y-%m')
            PocketMoneyPayout.objects.create(
                kid=kid,
                paid_by=request.user,
                points_at_payout=kid.total_points,
                amount_euros=amount_euros,
                note=form.cleaned_data.get('note', ''),
                month=month,
            )
            # Log the deduction
            deducted = -kid.total_points
            kid.add_points(deducted, reason=f"Pocket money payout: {family.currency_symbol}{amount_euros}", added_by=request.user)

            messages.success(request, f"Paid {family.currency_symbol}{amount_euros} to {kid.display_name}! Points reset. 💰")
            return redirect('accounts:kid_profile', kid_id=kid.pk)
    else:
        form = PayoutForm()

    return render(request, 'chores/payout.html', {
        'kid': kid, 'form': form,
        'amount_euros': amount_euros,
        'currency_symbol': family.currency_symbol,
    })


# ─── History & Reports ────────────────────────────────────────────────────────

@login_required
def transaction_history(request, kid_id=None):
    if kid_id:
        kid = get_object_or_404(User, pk=kid_id, family=request.user.family)
    else:
        kid = request.user

    transactions = PointTransaction.objects.filter(user=kid).order_by('-created_at')
    payouts = PocketMoneyPayout.objects.filter(kid=kid).order_by('-paid_at')

    return render(request, 'chores/history.html', {
        'kid': kid,
        'transactions': transactions,
        'payouts': payouts,
    })


@login_required
@parent_required
def export_csv(request, kid_id):
    """Export a kid's transaction history as CSV."""
    kid = get_object_or_404(User, pk=kid_id, family=request.user.family)
    transactions = PointTransaction.objects.filter(user=kid).order_by('-created_at')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{kid.display_name}_history.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Points', 'Balance After', 'Reason', 'Created By'])
    for t in transactions:
        writer.writerow([
            t.created_at.strftime('%Y-%m-%d %H:%M'),
            t.points,
            t.balance_after,
            t.reason,
            t.created_by.display_name if t.created_by else 'System',
        ])
    return response
