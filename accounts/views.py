from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST


def login_view(request):
    """Login page — redirects authenticated users straight to dashboard."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Honour ?next= param if present
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'accounts/login.html')


def register_view(request):
    """Registration page with server-side validation."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        full_name   = request.POST.get('full_name', '').strip()
        email       = request.POST.get('email', '').strip()
        username    = request.POST.get('username', '').strip()
        password    = request.POST.get('password', '')
        password2   = request.POST.get('password2', '')

        errors = []

        # --- Validate fields ---
        if not full_name:
            errors.append('Full name is required.')
        if not email:
            errors.append('Email address is required.')
        if not username:
            errors.append('Username is required.')

        # Uniqueness checks
        if username and User.objects.filter(username__iexact=username).exists():
            errors.append(f'The username "{username}" is already taken.')
        if email and User.objects.filter(email__iexact=email).exists():
            errors.append(f'An account with email "{email}" already exists.')

        # Password checks
        if password != password2:
            errors.append('Passwords do not match.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        if password.isdigit():
            errors.append('Password cannot be entirely numeric.')

        if errors:
            for err in errors:
                messages.error(request, err)
            # Re-render preserving previously entered values
            context = {
                'form_data': {
                    'full_name': full_name,
                    'email': email,
                    'username': username,
                }
            }
            return render(request, 'accounts/register.html', context)

        # --- Create user ---
        first_name, *rest = full_name.split(' ', 1)
        last_name = rest[0] if rest else ''
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        messages.success(request, f'Account created successfully! Welcome, {user.first_name}. Please log in.')
        return redirect('login')

    return render(request, 'accounts/register.html')


@login_required
def profile_view(request):
    """Profile & Settings — update info and change password."""
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        # ---- Update profile info ----
        if action == 'update_profile':
            full_name = request.POST.get('full_name', '').strip()
            email     = request.POST.get('email', '').strip()

            errors = []
            if not full_name:
                errors.append('Full name is required.')
            if not email:
                errors.append('Email address is required.')
            if email and User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                errors.append(f'The email "{email}" is already used by another account.')

            if errors:
                for err in errors:
                    messages.error(request, err)
            else:
                first_name, *rest = full_name.split(' ', 1)
                user.first_name = first_name
                user.last_name  = rest[0] if rest else ''
                user.email      = email
                user.save()
                messages.success(request, 'Profile updated successfully.')
            return redirect('profile')

        # ---- Change password ----
        if action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password     = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            errors = []
            if not user.check_password(current_password):
                errors.append('Current password is incorrect.')
            if new_password != confirm_password:
                errors.append('New passwords do not match.')
            if len(new_password) < 8:
                errors.append('New password must be at least 8 characters long.')
            if new_password.isdigit():
                errors.append('New password cannot be entirely numeric.')

            if errors:
                for err in errors:
                    messages.error(request, err)
            else:
                user.set_password(new_password)
                user.save()
                # Keep the user logged in after password change
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')
            return redirect('profile')

    return render(request, 'accounts/profile.html', {'profile_user': user})


@require_POST
@login_required
def logout_view(request):
    """POST-only logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')
