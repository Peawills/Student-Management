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
def staff_login(request):
    # Redirect if already logged in as staff
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("records:student_list")
        # Log out non-staff users
        logout(request)
        messages.warning(
            request, "You were logged out because you don't have staff access."
        )

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                # Redirect to next page if specified, otherwise to records:student_list
                next_url = (
                    request.GET.get("next")
                    or request.POST.get("next")
                    or "records:student_list"
                )
                return redirect(next_url)
            else:
                messages.error(request, "Only staff users can log in here.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


@login_required(login_url="accounts:login")
def staff_logout(request):
    username = request.user.username
    logout(request)
    messages.info(request, f"You have been logged out successfully, {username}.")
    return redirect("accounts:login")


@login_required(login_url="accounts:login")
@user_passes_test(lambda u: u.is_superuser)
def user_list(request):
    users = User.objects.all().order_by("-date_joined")
    return render(request, "accounts/user_list.html", {"users": users})


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
