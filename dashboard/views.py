from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from chores.models import ChoreAssignment, PointTransaction
from calendar_tasks.models import CalendarTaskAssignment
from accounts.models import User


@login_required
def home(request):
    user = request.user
    family = user.family

    if not family:
        return render(request, 'dashboard/no_family.html')

    kids = User.objects.filter(family=family, role=User.ROLE_CHILD).order_by('-total_points')

    # Count all pending approvals: both chore assignments and calendar task assignments
    chore_pending = ChoreAssignment.objects.filter(
        chore__family=family, status=ChoreAssignment.STATUS_COMPLETED
    ).count()
    calendar_pending = CalendarTaskAssignment.objects.filter(
        task__family=family, status=CalendarTaskAssignment.STATUS_COMPLETED
    ).count()
    pending_approvals_count = chore_pending + calendar_pending

    if user.is_parent:
        ctx = _parent_dashboard(request, family, kids, pending_approvals_count)
    else:
        ctx = _kid_dashboard(request, user)

    ctx.update({
        'kids': kids,
        'pending_approvals_count': pending_approvals_count,
        'family': family,
    })
    return render(request, 'dashboard/home.html', ctx)


def _parent_dashboard(request, family, kids, pending_count):
    """Extra context for parent dashboard."""
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)

    # Recent transactions across all kids
    recent_activity = PointTransaction.objects.filter(
        user__family=family
    ).order_by('-created_at')[:10]

    # Monthly stats per kid
    monthly_stats = []
    for kid in kids:
        approved_this_month = ChoreAssignment.objects.filter(
            assigned_to=kid, status=ChoreAssignment.STATUS_APPROVED,
            approved_at__gte=month_start
        )
        monthly_stats.append({
            'kid': kid,
            'chores_done': approved_this_month.count(),
            'points_earned': sum(a.points_awarded or 0 for a in approved_this_month),
        })

    all_pending = ChoreAssignment.objects.filter(
        chore__family=family, status=ChoreAssignment.STATUS_COMPLETED
    ).select_related('chore', 'assigned_to')[:5]

    overdue = ChoreAssignment.objects.filter(
        chore__family=family,
        status=ChoreAssignment.STATUS_PENDING,
        due_date__lt=now
    ).select_related('chore', 'assigned_to')

    return {
        'recent_activity': recent_activity,
        'monthly_stats': monthly_stats,
        'all_pending': all_pending,
        'overdue': overdue,
    }


def _kid_dashboard(request, user):
    """Extra context for kid dashboard."""
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)

    my_pending = ChoreAssignment.objects.filter(
        assigned_to=user, status=ChoreAssignment.STATUS_PENDING
    ).order_by('due_date')[:5]

    my_awaiting = ChoreAssignment.objects.filter(
        assigned_to=user, status=ChoreAssignment.STATUS_COMPLETED
    )

    recent_transactions = PointTransaction.objects.filter(user=user).order_by('-created_at')[:8]

    # Monthly earnings
    this_month_pts = PointTransaction.objects.filter(
        user=user, created_at__gte=month_start, points__gt=0
    )
    monthly_earned = sum(t.points for t in this_month_pts)

    chores_this_month = ChoreAssignment.objects.filter(
        assigned_to=user, status=ChoreAssignment.STATUS_APPROVED,
        approved_at__gte=month_start
    ).count()

    # Leaderboard rank
    all_kids = list(User.objects.filter(family=user.family, role=User.ROLE_CHILD).order_by('-total_points'))
    rank = next((i + 1 for i, k in enumerate(all_kids) if k.pk == user.pk), None)

    return {
        'my_pending': my_pending,
        'my_awaiting': my_awaiting,
        'recent_transactions': recent_transactions,
        'monthly_earned': monthly_earned,
        'chores_this_month': chores_this_month,
        'rank': rank,
        'total_kids': len(all_kids),
    }


@login_required
def leaderboard(request):
    family = request.user.family
    kids = User.objects.filter(family=family, role=User.ROLE_CHILD).order_by('-total_points')
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    week_start = now - timedelta(days=now.weekday())

    leaderboard_data = []
    for i, kid in enumerate(kids):
        monthly = ChoreAssignment.objects.filter(
            assigned_to=kid, status=ChoreAssignment.STATUS_APPROVED,
            approved_at__gte=month_start
        )
        weekly = ChoreAssignment.objects.filter(
            assigned_to=kid, status=ChoreAssignment.STATUS_APPROVED,
            approved_at__gte=week_start
        )
        leaderboard_data.append({
            'rank': i + 1,
            'kid': kid,
            'monthly_chores': monthly.count(),
            'monthly_points': sum(a.points_awarded or 0 for a in monthly),
            'weekly_chores': weekly.count(),
            'weekly_points': sum(a.points_awarded or 0 for a in weekly),
            'badges': kid.badges.all(),
        })

    return render(request, 'dashboard/leaderboard.html', {
        'leaderboard_data': leaderboard_data,
        'family': family,
    })
