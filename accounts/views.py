from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User
from .forms import UserCreateForm, UserUpdateForm  # ← Add UserUpdateForm here


@csrf_protect
@never_cache
def custom_login_view(request):
    """
    A unified login view for all user types (students, parents, staff).
    It authenticates the user and redirects them to the portal dashboard,
    which then routes them to their specific interface.
    """
    # If user is already logged in, send them to the portal dashboard
    if request.user.is_authenticated:
        return redirect("portal:dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(
                request, f"Welcome back, {user.get_full_name() or user.username}!"
            )
            # Redirect to the main portal dashboard, which will handle routing.
            # Or to the 'next' URL if it was provided (e.g., by @login_required)
            next_url = request.GET.get("next") or "portal:dashboard"
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    # Determine the login type from the query parameter for dynamic title
    login_type = request.GET.get("type", "general").lower()
    if login_type == "student":
        page_title = "Student Portal Login"
    elif login_type == "parent":
        page_title = "Parent Portal Login"
    elif login_type == "staff":
        page_title = "Staff / Admin Portal Login"
    elif login_type == "admin":
        page_title = "Admin Portal Login"
    else:
        page_title = "Portal Login"  # Default title

    return render(
        request, "accounts/login.html", {"form": form, "page_title": page_title}
    )


@login_required(login_url="accounts:login")
def staff_logout(request):
    username = request.user.username
    logout(request)
    messages.info(request, f"You have been logged out successfully, {username}.")
    return redirect("accounts:login")


@login_required(login_url="accounts:login")
@user_passes_test(lambda u: u.is_superuser)
def user_list(request):
    """
    Display a list of users, with the ability to filter by role (admin, staff, parent, student).
    """
    user_type = request.GET.get("type")
    users_qs = User.objects.all().select_related("student_profile", "parent_profile").order_by("-date_joined")

    page_title = "All Users"

    if user_type == "student":
        users_qs = users_qs.filter(student_profile__isnull=False)
        page_title = "Student Users"
    elif user_type == "parent":
        users_qs = users_qs.filter(parent_profile__isnull=False)
        page_title = "Parent Users"
    elif user_type == "staff":
        users_qs = users_qs.filter(is_staff=True, is_superuser=False)
        page_title = "Staff Users"
    elif user_type == "admin":
        users_qs = users_qs.filter(is_superuser=True)
        page_title = "Admin Users"

    context = {
        "users": users_qs,
        "page_title": page_title,
        "current_filter": user_type or "all",
    }
    return render(request, "accounts/user_list.html", context)


@login_required(login_url="accounts:login")
@user_passes_test(lambda u: u.is_superuser)
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(
                    request, f"User '{user.username}' was created successfully!"
                )
                return redirect("accounts:user_list")
            except Exception as e:
                messages.error(request, f"Error creating user: {str(e)}")
        else:
            # Add form-level errors to messages
            for field in form.errors:
                messages.error(request, f"{field}: {' '.join(form.errors[field])}")
    else:
        form = UserCreateForm()

    return render(request, "accounts/user_form.html", {"form": form})


@login_required(login_url="accounts:login")
@user_passes_test(lambda u: u.is_superuser)
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, "accounts/user_detail.html", {"user_detail": user})


@login_required(login_url="accounts:login")
@user_passes_test(lambda u: u.is_superuser)
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)  # ← Changed here
        if form.is_valid():
            user = form.save()
            messages.success(
                request, f"User '{user.username}' was updated successfully!"
            )
            return redirect("accounts:user_list")
    else:
        form = UserUpdateForm(instance=user)  # ← Changed here

    return render(request, "accounts/user_form.html", {"form": form})


@login_required(login_url="accounts:login")
@user_passes_test(lambda u: u.is_superuser)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user.delete()
        messages.success(request, f"User '{user.username}' was deleted successfully!")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_confirm_delete.html", {"user": user})
