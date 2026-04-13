from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from .models import User, Family
from .forms import (
    FamilyRegistrationForm, JoinFamilyForm, CustomLoginForm, AddChildForm,
    AdjustPointsForm, PasswordResetRequestForm, PasswordResetForm
)


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return render(request, 'accounts/landing.html')


def register_family(request):
    """Parent registers and creates a new family."""
    if request.method == 'POST':
        form = FamilyRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                family = Family.objects.create(
                    name=form.cleaned_data['family_name'],
                    currency_symbol=form.cleaned_data['currency_symbol'],
                )
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password1'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data.get('last_name', ''),
                    family=family,
                    role=User.ROLE_PARENT,
                    avatar='👨‍👩‍👧‍👦',
                )
            login(request, user)
            messages.success(request, f"Welcome! Your family code is: {family.invite_code}")
            return redirect('dashboard:home')
    else:
        form = FamilyRegistrationForm()
    return render(request, 'accounts/register_family.html', {'form': form})


def join_family(request):
    """Child joins with invite code."""
    if request.method == 'POST':
        form = JoinFamilyForm(request.POST)
        if form.is_valid():
            family = form.cleaned_data['invite_code']
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                family=family,
                role=User.ROLE_CHILD,
                avatar=form.cleaned_data['avatar'],
            )
            login(request, user)
            messages.success(request, f"Welcome to {family.name}! 🎉")
            return redirect('dashboard:home')
    else:
        form = JoinFamilyForm()
    return render(request, 'accounts/join_family.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.display_name}! 👋")
            return redirect(request.GET.get('next', 'dashboard:home'))
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "See you next time! 👋")
    return redirect('accounts:login')


@login_required
def profile(request):
    return render(request, 'accounts/profile.html')


@login_required
def kid_profile(request, kid_id):
    """View a specific kid's profile (parent or self)."""
    kid = get_object_or_404(User, pk=kid_id, family=request.user.family)
    from chores.models import PointTransaction, ChoreAssignment
    transactions = PointTransaction.objects.filter(user=kid).order_by('-created_at')[:20]
    completed_chores = ChoreAssignment.objects.filter(
        assigned_to=kid, status=ChoreAssignment.STATUS_APPROVED
    ).count()
    ctx = {
        'kid': kid,
        'transactions': transactions,
        'completed_chores': completed_chores,
    }
    return render(request, 'accounts/kid_profile.html', ctx)


@login_required
def adjust_points(request, kid_id):
    """Parent adjusts points manually."""
    if not request.user.is_parent:
        messages.error(request, "Only parents can adjust points.")
        return redirect('dashboard:home')
    kid = get_object_or_404(User, pk=kid_id, family=request.user.family, role=User.ROLE_CHILD)
    if request.method == 'POST':
        form = AdjustPointsForm(request.POST)
        if form.is_valid():
            pts = form.cleaned_data['points']
            reason = form.cleaned_data.get('reason') or 'Manual adjustment by parent'
            kid.add_points(pts, reason=reason, added_by=request.user)
            action = "Added" if pts > 0 else "Deducted"
            messages.success(request, f"{action} {abs(pts)} points for {kid.display_name}!")
            return redirect('accounts:kid_profile', kid_id=kid.pk)
    else:
        form = AdjustPointsForm()
    return render(request, 'accounts/adjust_points.html', {'form': form, 'kid': kid})


# ─── Password Reset Views ───────────────────────────────────────────────────

def password_reset_request(request):
    """User requests password reset."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            user = User.objects.filter(
                username=username_or_email
            ).first() or User.objects.filter(email=username_or_email).first()

            if user:
                # Generate reset token
                token = user.generate_password_reset_token()

                # Send email with reset link
                reset_url = request.build_absolute_uri(
                    reverse('accounts:password_reset', kwargs={'token': token})
                )

                subject = "🔐 Reset your ChoreTracker password"
                message = f"""
Hello {user.first_name or user.username},

We received a request to reset your password. Click the link below to reset it:

{reset_url}

If you didn't request this, you can ignore this email.

This link expires in 24 hours.

Best regards,
ChoreTracker Team
                """

                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email] if user.email else [],
                        fail_silently=False,
                    )
                except Exception as e:
                    messages.warning(request, "Could not send email, but token was generated.")
                    # Still allow token-based reset if email fails

            # Always show success message for security
            messages.success(
                request,
                "If an account with that username/email exists, a password reset link has been sent to the email address. 📧"
            )
            return redirect('accounts:login')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset(request, token):
    """Reset password with token."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    try:
        user = User.objects.get(password_reset_token=token)
    except User.DoesNotExist:
        messages.error(request, "Invalid or expired reset link.")
        return redirect('accounts:password_reset_request')

    if not user.is_password_reset_token_valid():
        messages.error(request, "This reset link has expired. Please request a new one.")
        return redirect('accounts:password_reset_request')

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password1'])
            user.clear_password_reset_token()
            messages.success(request, "Your password has been reset successfully! 🎉")
            return redirect('accounts:login')
    else:
        form = PasswordResetForm()

    return render(request, 'accounts/password_reset.html', {'form': form, 'token': token})
