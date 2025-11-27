# academics/lock_views.py
"""
Score Locking System Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import models
from django.utils import timezone

from .models import Assessment


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def lock_assessment_scores(request, pk):
    """Lock all scores for an assessment - only admin can unlock"""
    assessment = get_object_or_404(Assessment, pk=pk)

    if assessment.is_locked:
        messages.warning(request, "Assessment scores are already locked.")
    else:
        assessment.lock_scores(admin_user=request.user)
        messages.success(
            request,
            f"✓ Assessment '{assessment.title}' has been LOCKED. "
            f"Only admins can modify scores.",
        )

    return redirect(
        request.META.get("HTTP_REFERER", f"/academics/assessments/{assessment.pk}/")
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def unlock_assessment_scores(request, pk):
    """Unlock all scores for an assessment"""
    assessment = get_object_or_404(Assessment, pk=pk)

    if not assessment.is_locked:
        messages.warning(request, "Assessment scores are not locked.")
    else:
        locked_by_name = (
            assessment.locked_by.get_full_name() or assessment.locked_by.username
            if assessment.locked_by
            else "Unknown"
        )
        assessment.unlock_scores()
        messages.success(
            request,
            f"✓ Assessment '{assessment.title}' has been UNLOCKED. "
            f"Teachers can now modify scores (was locked by {locked_by_name}).",
        )

    return redirect(
        request.META.get("HTTP_REFERER", f"/academics/assessments/{assessment.pk}/")
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def lock_management_dashboard(request):
    """Dashboard to view and manage locked assessments"""

    # Get all assessments with lock info
    locked_assessments = (
        Assessment.objects.filter(is_locked=True)
        .select_related(
            "locked_by",
            "assignment__subject",
            "assignment__classroom",
            "assessment_type",
        )
        .order_by("-locked_at")
    )

    unlocked_assessments = (
        Assessment.objects.filter(is_locked=False)
        .select_related(
            "assignment__subject", "assignment__classroom", "assessment_type"
        )
        .order_by("-date")
    )

    # Paginate
    paginator_locked = Paginator(locked_assessments, 20)
    page_locked = request.GET.get("page_locked", 1)
    locked_page = paginator_locked.get_page(page_locked)

    paginator_unlocked = Paginator(unlocked_assessments, 20)
    page_unlocked = request.GET.get("page_unlocked", 1)
    unlocked_page = paginator_unlocked.get_page(page_unlocked)

    context = {
        "locked_assessments": locked_page,
        "unlocked_assessments": unlocked_page,
        "total_locked": paginator_locked.count,
        "total_unlocked": paginator_unlocked.count,
    }

    return render(request, "academics/lock_management.html", context)


@login_required
def validate_assessment_constraints(request, pk):
    """AJAX endpoint to validate assessment score constraints"""
    assessment = get_object_or_404(Assessment, pk=pk)

    validation_result = {
        "assessment_code": assessment.assessment_code,
        "max_score": assessment.max_score,
        "is_valid": True,
        "errors": [],
        "warnings": [],
    }

    # Validate assessment code constraints
    if assessment.assessment_code.startswith("CA"):
        if assessment.max_score > 10:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"CA assessments cannot exceed 10 points (current: {assessment.max_score})"
            )

        # Check total CA
        ca_total = (
            Assessment.objects.filter(
                assignment__classroom=assessment.assignment.classroom,
                assignment__subject=assessment.assignment.subject,
                assignment__term=assessment.assignment.term,
                assessment_code__startswith="CA",
            )
            .exclude(pk=assessment.pk)
            .aggregate(total=models.Sum("max_score"))["total"]
            or 0
        )

        if ca_total + assessment.max_score > 40:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Total CA cannot exceed 40 points. "
                f"Current: {ca_total}, trying to add: {assessment.max_score}"
            )
        else:
            validation_result["warnings"].append(
                f"CA Total: {ca_total} + {assessment.max_score} = {ca_total + assessment.max_score}/40"
            )

    elif assessment.assessment_code == "TEST":
        if assessment.max_score > 10:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Test assessments cannot exceed 10 points (current: {assessment.max_score})"
            )

    elif assessment.assessment_code == "EXAM":
        if assessment.max_score != 60:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Exam must be exactly 60 points (current: {assessment.max_score})"
            )

    # Lock status info
    validation_result["is_locked"] = assessment.is_locked
    if assessment.is_locked:
        validation_result["locked_by"] = (
            assessment.locked_by.get_full_name() or assessment.locked_by.username
            if assessment.locked_by
            else "Unknown Admin"
        )
        validation_result["locked_at"] = (
            assessment.locked_at.isoformat() if assessment.locked_at else None
        )

    return JsonResponse(validation_result)
