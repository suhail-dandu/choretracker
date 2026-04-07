from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User, Family, Badge
from accounts.forms import AddChildForm


def parent_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_parent:
            messages.error(request, "Only parents can do that! 🔒")
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def family_overview(request):
    family = request.user.family
    kids = User.objects.filter(family=family, role=User.ROLE_CHILD).order_by('first_name')
    parents = User.objects.filter(family=family, role=User.ROLE_PARENT)
    return render(request, 'family/overview.html', {
        'family': family,
        'kids': kids,
        'parents': parents,
    })


@login_required
@parent_required
def add_child(request):
    if request.method == 'POST':
        form = AddChildForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.family = request.user.family
            child.role = User.ROLE_CHILD
            child.set_password(form.cleaned_data['password'])
            child.save()
            messages.success(request, f"Added {child.display_name} to the family! 🎉")
            return redirect('family:overview')
    else:
        form = AddChildForm()
    return render(request, 'family/add_child.html', {'form': form})


@login_required
@parent_required
def remove_child(request, kid_id):
    kid = get_object_or_404(User, pk=kid_id, family=request.user.family, role=User.ROLE_CHILD)
    if request.method == 'POST':
        kid.family = None
        kid.save()
        messages.success(request, f"{kid.display_name} has been removed from the family.")
        return redirect('family:overview')
    return render(request, 'family/remove_child.html', {'kid': kid})


@login_required
@parent_required
def award_badge(request, kid_id):
    kid = get_object_or_404(User, pk=kid_id, family=request.user.family, role=User.ROLE_CHILD)
    if request.method == 'POST':
        badge_type = request.POST.get('badge_type')
        if badge_type:
            badge, created = Badge.objects.get_or_create(
                user=kid, badge_type=badge_type,
                defaults={'awarded_by': request.user}
            )
            if created:
                messages.success(request, f"Badge awarded to {kid.display_name}! 🏆")
            else:
                messages.info(request, f"{kid.display_name} already has that badge.")
        return redirect('accounts:kid_profile', kid_id=kid.pk)
    return render(request, 'family/award_badge.html', {
        'kid': kid,
        'badge_choices': Badge.BADGE_TYPES,
        'existing_badges': [b.badge_type for b in kid.badges.all()],
    })


@login_required
@parent_required
def family_settings(request):
    family = request.user.family
    if request.method == 'POST':
        family.name = request.POST.get('family_name', family.name)
        family.currency_symbol = request.POST.get('currency_symbol', family.currency_symbol)
        pts = request.POST.get('points_per_unit')
        if pts and pts.isdigit():
            family.points_per_unit = int(pts)
        family.save()
        messages.success(request, "Family settings updated!")
        return redirect('family:overview')
    return render(request, 'family/settings.html', {'family': family})
