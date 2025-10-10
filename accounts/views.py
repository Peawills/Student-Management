from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect


@csrf_protect
@never_cache
def staff_login(request):
    # Redirect if already logged in as staff
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("student_list")
        # Log out non-staff users
        logout(request)
        messages.warning(request, "You were logged out because you don't have staff access.")
    
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                # Redirect to next page if specified, otherwise to student_list
                next_url = request.GET.get('next') or request.POST.get('next') or 'student_list'
                return redirect(next_url)
            else:
                messages.error(request, "Only staff users can log in here.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, "accounts/login.html", {"form": form})


@login_required(login_url='staff_login')  # Update this to match your URL name
def staff_logout(request):
    username = request.user.username
    logout(request)
    messages.info(request, f"You have been logged out successfully, {username}.")
    # Fix: Use the correct URL name without namespace if not using one
    return redirect("staff_login")  # Change from "accounts:login" to your actual URL name