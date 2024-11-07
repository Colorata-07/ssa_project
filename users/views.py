from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from django.contrib import messages 
import requests
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse

# Set up logger
logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            logger.info(f"User '{user.username}' logged in successfully.")  # Log successful login
            return redirect('home')
        else:
            logger.warning(f"Failed login attempt for username '{username}'.")  # Log failed login
            messages.error(request, "Invalid credentials.")
    return render(request, 'users/login.html')

def logout_view(request):
    logger.info(f"User '{request.user.username}' logged out.")  # Log logout
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect(reverse('login'))

@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()  # Deletes the user's account and all related data
        messages.success(request, 'Your account has been deleted.')
        return redirect('home')
    return render(request, 'users/delete_account.html')

@login_required
def privacy_settings(request):
    if request.method == 'POST':
        request.user.is_profile_public = request.POST.get('is_profile_public', False)
        request.user.save()
        messages.success(request, 'Privacy settings updated.')
    return render(request, 'users/privacy_settings.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Automatically hashes the password before saving
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        recaptcha_response = request.POST.get("recaptcha-token")  # Updated
        # Verify reCAPTCHA
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response,
            'remoteip': request.META.get('REMOTE_ADDR'),
        }
        recaptcha_verification = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data=data
        )
        result = recaptcha_verification.json()
        # Check reCAPTCHA response
        if not result.get("success"):
            messages.error(request, "reCAPTCHA validation failed. Please try again.")
            return redirect("users:login")  # Redirect back to the login page
        # Authenticate user if reCAPTCHA is valid
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to the next URL if provided, else default to user profile
            next_url = request.GET.get('next', reverse("users:user"))  # Simplified fallback
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "users/login.html")


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Your account has been created! Please set up multi-factor authentication.")
            return redirect('two_factor:setup')  # Redirect to MFA setup page
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})