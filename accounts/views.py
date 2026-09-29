from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .forms import CustomerRegistrationForm, CustomerLoginForm, CustomerProfileUpdateForm
from .models import CustomerProfile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:customer_dashboard')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    full_name = form.cleaned_data['full_name'].strip()
                    parts = full_name.split(' ', 1)
                    first_name = parts[0]
                    last_name = parts[1] if len(parts) > 1 else ''

                    user = User.objects.create_user(
                        username=form.cleaned_data['username'].strip(),
                        email=form.cleaned_data['email'].strip().lower(),
                        password=form.cleaned_data['password'],
                        first_name=first_name,
                        last_name=last_name
                    )

                    # Update profile created via signal
                    profile, _ = CustomerProfile.objects.get_or_create(user=user)
                    profile.phone = form.cleaned_data['phone'].strip()
                    profile.save()

                    # Award welcome bonus loyalty points (e.g., 50 points!)
                    try:
                        from loyalty.models import LoyaltyPointTransaction
                        LoyaltyPointTransaction.objects.create(
                            customer=user,
                            points=50,
                            transaction_type='BONUS',
                            description='Welcome bonus points for joining Modern Coffee Shop'
                        )
                    except Exception:
                        pass

                    # Auto login after registration
                    login(request, user)
                    messages.success(request, f"Welcome to Modern Coffee Shop, {first_name}! You've been awarded 50 bonus loyalty points.")
                    return redirect('dashboard:customer_dashboard')
            except Exception as e:
                messages.error(request, f"An error occurred during registration: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form, 'title': 'Create an Account'})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:customer_dashboard')

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = CustomerLoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data['remember_me']

            # Allow login using either username or email
            user = None
            if '@' in username_or_email:
                try:
                    user_obj = User.objects.get(email__iexact=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except (User.DoesNotExist, User.MultipleObjectsReturned):
                    user = None
            
            if user is None:
                user = authenticate(request, username=username_or_email, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    if not remember_me:
                        # Session expires when user closes the browser
                        request.session.set_expiry(0)
                    else:
                        # Keep session for 2 weeks
                        request.session.set_expiry(1209600)

                    messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                    if next_url and next_url.startswith('/'):
                        return redirect(next_url)
                    return redirect('dashboard:customer_dashboard')
                else:
                    messages.error(request, "Your account has been deactivated. Please contact support.")
            else:
                messages.error(request, "Invalid username/email or password.")
        else:
            messages.error(request, "Please provide valid credentials.")
    else:
        form = CustomerLoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'title': 'Sign In', 'next': next_url})


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "You have been safely signed out. See you soon!")
    return redirect('home')


@login_required
def profile_view(request):
    user = request.user
    profile, _ = CustomerProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = CustomerProfileUpdateForm(request.POST, user=user)
        if form.is_valid():
            full_name = form.cleaned_data['full_name'].strip()
            parts = full_name.split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
            user.email = form.cleaned_data['email'].strip().lower()
            user.save()

            profile.phone = form.cleaned_data['phone'].strip()
            profile.address = form.cleaned_data['address'].strip()
            profile.save()

            messages.success(request, "Your profile details have been successfully updated.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors in the profile form.")
    else:
        initial_data = {
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'phone': profile.phone,
            'address': profile.address,
        }
        form = CustomerProfileUpdateForm(initial=initial_data, user=user)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
        'title': 'My Profile'
    })
