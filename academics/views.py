# academics/views.py
from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum, Max, Min
from django.http import HttpResponse, JsonResponse
import csv
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import transaction
import pandas as pd
from datetime import datetime
import json

from .models import (
    AcademicSession,
    Term,
    Subject,
    ClassRoom,
    SubjectAssignment,
    AssessmentType,
    Assessment,
    StudentScore,
    TermResult,
    ReportCard,
    PerformanceComment,
    Timetable,
    Attendance,
)
from .forms import (
    AcademicSessionForm,
    TermForm,
    SubjectForm,
    ClassRoomForm,
    SubjectAssignmentForm,
    AssessmentTypeForm,
    AssessmentForm,
    StudentScoreForm,
    BulkScoreEntryForm,
    TermResultForm,
    ReportCardForm,
    BulkReportCardGenerationForm,
    PerformanceFilterForm,
    ScoreImportForm,
    TimetableForm,
    PerformanceCommentForm,
)
from records.models import Student


# ============================================
# DASHBOARD & HOME
# ============================================


@login_required
def academics_dashboard(request):
    """Main academics dashboard"""
    current_term = Term.objects.filter(is_current=True).first()
    current_session = AcademicSession.objects.filter(is_current=True).first()

    # Get teacher's assignments if not admin
    if not request.user.is_superuser:
        assignments = SubjectAssignment.objects.filter(
            teacher=request.user, term=current_term
        )
    else:
        assignments = SubjectAssignment.objects.filter(term=current_term)

    # Statistics
    stats = {
        "total_students": Student.objects.count(),
        "total_subjects": Subject.objects.count(),
        "total_classes": ClassRoom.objects.filter(session=current_session).count(),
        "total_assessments": Assessment.objects.filter(
            assignment__term=current_term
        ).count()
        if current_term
        else 0,
        "pending_scores": StudentScore.objects.filter(
            assessment__assignment__term=current_term, score__isnull=True
        ).count()
        if current_term
        else 0,
    }

    # Recent assessments
    recent_assessments = (
        Assessment.objects.filter(assignment__teacher=request.user).order_by(
            "-created_at"
        )[:5]
        if not request.user.is_superuser
        else Assessment.objects.order_by("-created_at")[:5]
    )

    # Performance summary (if current term exists)
    performance_data = None
    if current_term:
        performance_data = TermResult.objects.filter(term=current_term).aggregate(
            avg_score=Avg("total_score"),
            highest_score=Max("total_score"),
            lowest_score=Min("total_score"),
        )

    # Prepare additional context keys expected by the dashboard template
    total_sessions = AcademicSession.objects.count()
    current_term_name = current_term.name if current_term else "-"
    total_classes = ClassRoom.objects.count()
    total_subjects = Subject.objects.count()
    pending_assessments = stats.get("pending_scores", 0)

    # Recent scores
    recent_scores = StudentScore.objects.select_related(
        "student", "assessment"
    ).order_by("-submitted_at")[:5]

    # Classes snapshot
    classes_qs = ClassRoom.objects.all()
    classes_snapshot = []
    for c in classes_qs:
        classes_snapshot.append(
            {
                "classroom": str(c),
                "class_teacher_name": c.class_teacher.get_full_name()
                if c.class_teacher
                else "-",
                "student_count": c.students.count(),
            }
        )

    context = {
        "current_term": current_term,
        "current_session": current_session,
        "assignments": assignments,
        "stats": stats,
        "recent_assessments": recent_assessments,
        "performance_data": performance_data,
        # Template-friendly variables
        "total_sessions": total_sessions,
        "current_term_name": current_term_name,
        "total_classes": total_classes,
        "total_subjects": total_subjects,
        "pending_assessments": pending_assessments,
        "recent_scores": recent_scores,
        "classes_snapshot": classes_snapshot,
    }

    return render(request, "academics/dashboard.html", context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def publication_center(request):
    """A central place to manage the publication status of assessments and report cards."""

    # Get current term for default filtering
    current_term = Term.objects.filter(is_current=True).first()

    # --- Filtering ---
    selected_term_id = request.GET.get(
        "term", current_term.id if current_term else None
    )
    selected_classroom_id = request.GET.get("classroom")

    # --- Assessments ---
    assessments_qs = Assessment.objects.select_related(
        "assignment__subject", "assignment__classroom", "assessment_type"
    ).order_by("-date")

    if selected_term_id:
        assessments_qs = assessments_qs.filter(assignment__term_id=selected_term_id)
    if selected_classroom_id:
        assessments_qs = assessments_qs.filter(
            assignment__classroom_id=selected_classroom_id
        )

    # --- Report Cards ---
    report_cards_qs = ReportCard.objects.select_related(
        "student", "term", "classroom"
    ).order_by("-term__start_date", "classroom__level", "student__surname")

    if selected_term_id:
        report_cards_qs = report_cards_qs.filter(term_id=selected_term_id)
    if selected_classroom_id:
        report_cards_qs = report_cards_qs.filter(classroom_id=selected_classroom_id)

    # --- Context ---
    context = {
        "assessments": assessments_qs,
        "report_cards": report_cards_qs,
        "terms": Term.objects.all().order_by("-start_date"),
        "classrooms": ClassRoom.objects.filter(session__is_current=True).order_by(
            "level", "arm"
        ),
        "selected_term_id": int(selected_term_id) if selected_term_id else None,
        "selected_classroom_id": int(selected_classroom_id)
        if selected_classroom_id
        else None,
    }

    return render(request, "academics/publication_center.html", context)


# ============================================
# ACADEMIC SESSION & TERM MANAGEMENT
# ============================================


@login_required
@user_passes_test(lambda u: u.is_superuser)
def session_list(request):
    """List all academic sessions"""
    sessions = AcademicSession.objects.all().order_by("-start_date")
    return render(request, "academics/session_list.html", {"sessions": sessions})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def session_create(request):
    """Create new academic session"""
    if request.method == "POST":
        form = AcademicSessionForm(request.POST)
        if form.is_valid():
            session = form.save()
            messages.success(
                request, f'Academic session "{session.name}" created successfully!'
            )
            return redirect("academics:session_list")
    else:
        form = AcademicSessionForm()

    return render(
        request, "academics/session_form.html", {"form": form, "action": "Create"}
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def session_update(request, pk):
    """Update academic session"""
    session = get_object_or_404(AcademicSession, pk=pk)

    if request.method == "POST":
        form = AcademicSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, "Academic session updated successfully!")
            return redirect("academics:session_list")
    else:
        form = AcademicSessionForm(instance=session)

    return render(
        request,
        "academics/session_form.html",
        {"form": form, "session": session, "action": "Update"},
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def session_delete(request, pk):
    """Delete academic session"""
    session = get_object_or_404(AcademicSession, pk=pk)

    if request.method == "POST":
        session_name = session.name
        session.delete()
        messages.success(
            request, f'Academic session "{session_name}" deleted successfully!'
        )
        return redirect("academics:session_list")

    return render(
        request, "academics/session_confirm_delete.html", {"session": session}
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def term_list(request):
    """List all terms"""
    terms = Term.objects.all().order_by("-session__start_date", "name")
    return render(request, "academics/term_list.html", {"terms": terms})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def term_create(request):
    """Create new term"""
    if request.method == "POST":
        form = TermForm(request.POST)
        if form.is_valid():
            term = form.save()
            messages.success(request, f'Term "{term}" created successfully!')
            return redirect("academics:term_list")
    else:
        form = TermForm()

    return render(
        request, "academics/term_form.html", {"form": form, "action": "Create"}
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def term_update(request, pk):
    """Update term"""
    term = get_object_or_404(Term, pk=pk)

    if request.method == "POST":
        form = TermForm(request.POST, instance=term)
        if form.is_valid():
            form.save()
            messages.success(request, "Term updated successfully!")
            return redirect("academics:term_list")
    else:
        form = TermForm(instance=term)

    return render(
        request,
        "academics/term_form.html",
        {"form": form, "term": term, "action": "Update"},
    )


# ============================================
# SUBJECT MANAGEMENT
# ============================================


@login_required
def subject_list(request):
    """List all subjects"""
    subjects = Subject.objects.all().order_by("name")

    # Search
    query = request.GET.get("q")
    if query:
        subjects = subjects.filter(Q(name__icontains=query) | Q(code__icontains=query))

    return render(
        request, "academics/subject_list.html", {"subjects": subjects, "query": query}
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def subject_create(request):
    """Create new subject"""
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject "{subject.name}" created successfully!')
            return redirect("academics:subject_list")
    else:
        form = SubjectForm()

    return render(
        request, "academics/subject_form.html", {"form": form, "action": "Create"}
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def subject_update(request, pk):
    """Update subject"""
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, "Subject updated successfully!")
            return redirect("academics:subject_list")
    else:
        form = SubjectForm(instance=subject)

    return render(
        request,
        "academics/subject_form.html",
        {"form": form, "subject": subject, "action": "Update"},
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def subject_delete(request, pk):
    """Delete subject"""
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == "POST":
        subject_name = subject.name
        subject.delete()
        messages.success(request, f'Subject "{subject_name}" deleted successfully!')
        return redirect("academics:subject_list")

    return render(
        request, "academics/subject_confirm_delete.html", {"subject": subject}
    )


# ============================================
# CLASS MANAGEMENT
# ============================================


@login_required
def classroom_list(request):
    """List all classrooms"""
    classrooms = ClassRoom.objects.all().order_by("level", "arm")
    current_session = AcademicSession.objects.filter(is_current=True).first()

    if current_session:
        classrooms = classrooms.filter(session=current_session)

    return render(
        request,
        "academics/classroom_list.html",
        {"classrooms": classrooms, "current_session": current_session},
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def classroom_create(request):
    """Create new classroom"""
    if request.method == "POST":
        form = ClassRoomForm(request.POST)
        if form.is_valid():
            classroom = form.save()
            messages.success(request, f'Class "{classroom}" created successfully!')
            return redirect("academics:classroom_list")
    else:
        form = ClassRoomForm()

    return render(
        request, "academics/classroom_form.html", {"form": form, "action": "Create"}
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def classroom_update(request, pk):
    """Update classroom"""
    classroom = get_object_or_404(ClassRoom, pk=pk)

    if request.method == "POST":
        form = ClassRoomForm(request.POST, instance=classroom)
        if form.is_valid():
            form.save()
            messages.success(request, "Class updated successfully!")
            return redirect("academics:classroom_list")
    else:
        form = ClassRoomForm(instance=classroom)

    return render(
        request,
        "academics/classroom_form.html",
        {"form": form, "classroom": classroom, "action": "Update"},
    )


@login_required
def classroom_detail(request, pk):
    """Enhanced classroom detail with student management"""
    classroom = get_object_or_404(ClassRoom, pk=pk)

    # Get students in this classroom
    students = Student.objects.filter(classroom=classroom).order_by(
        "surname", "other_name"
    )

    # Get gender counts
    male_count = students.filter(sex="M").count()
    female_count = students.filter(sex="F").count()

    # Get subjects assigned to this class
    subjects = SubjectAssignment.objects.filter(
        classroom=classroom, term__is_current=True
    ).select_related("subject", "teacher")

    # Get available students (not in any class or in current session classes)
    available_students = Student.objects.filter(
        Q(classroom__isnull=True) | ~Q(classroom__session=classroom.session)
    ).order_by("surname", "other_name")

    # Get all classrooms for the 'Move Student' modal, excluding the current one
    all_classrooms = (
        ClassRoom.objects.filter(session=classroom.session)
        .exclude(pk=pk)
        .order_by("level", "arm")
    )

    context = {
        "classroom": classroom,
        "students": students,
        "male_count": male_count,
        "female_count": female_count,
        "subjects": subjects,
        "available_students": available_students,
        "all_classrooms": all_classrooms,
    }

    return render(request, "academics/classroom_detail.html", context)


@login_required
def add_students_to_class(request, pk):
    """Add selected students to a classroom"""
    classroom = get_object_or_404(ClassRoom, pk=pk)

    if request.method == "POST":
        student_ids = request.POST.getlist("students")

        if student_ids:
            added_count = 0
            updated_count = 0

            for student_id in student_ids:
                try:
                    student = Student.objects.get(id=student_id)

                    # Check if student is already in another class
                    if student.classroom and student.classroom != classroom:
                        # Student is moving from another class
                        old_class = student.classroom
                        student.classroom = classroom
                        student.class_at_present = str(classroom)
                        student.save()
                        updated_count += 1
                        messages.info(
                            request,
                            f"{student.full_name} moved from {old_class} to {classroom}",
                        )
                    else:
                        # New assignment
                        student.classroom = classroom
                        student.class_at_present = str(classroom)
                        student.save()
                        added_count += 1

                except Student.DoesNotExist:
                    continue

            if added_count > 0:
                messages.success(
                    request,
                    f"Successfully added {added_count} student(s) to {classroom}",
                )

            if updated_count > 0:
                messages.success(
                    request,
                    f"Successfully moved {updated_count} student(s) to {classroom}",
                )
        else:
            messages.warning(request, "No students selected.")

    return redirect("academics:classroom_detail", pk=pk)


@login_required
def remove_student_from_class(request, classroom_pk, student_pk):
    """Remove a student from a classroom"""
    classroom = get_object_or_404(ClassRoom, pk=classroom_pk)
    student = get_object_or_404(Student, pk=student_pk)

    if request.method == "POST":
        if student.classroom == classroom:
            student.classroom = None
            student.class_at_present = ""
            student.save()
            messages.success(request, f"{student.full_name} removed from {classroom}")
        else:
            messages.error(request, f"{student.full_name} is not in {classroom}")

    return redirect("academics:classroom_detail", pk=classroom_pk)


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def move_student_to_class(request):
    """Move a student to a different class."""
    student_id = request.POST.get("student_id")
    new_classroom_id = request.POST.get("new_classroom_id")
    origin_classroom_pk = request.POST.get("origin_classroom_pk")

    if not all([student_id, new_classroom_id, origin_classroom_pk]):
        messages.error(request, "Invalid request. Missing required data.")
        return redirect("academics:classroom_list")

    student = get_object_or_404(Student, id=student_id)
    new_classroom = get_object_or_404(ClassRoom, id=new_classroom_id)
    old_classroom_name = str(student.classroom)

    student.classroom = new_classroom
    student.class_at_present = str(new_classroom)
    student.save()

    messages.success(
        request,
        f"Moved {student.full_name} from {old_classroom_name} to {new_classroom}.",
    )
    return redirect("academics:classroom_detail", pk=origin_classroom_pk)


# ============================================
# SUBJECT ASSIGNMENT
# ============================================


@login_required
@user_passes_test(lambda u: u.is_superuser)
def assignment_list(request):
    """List all subject assignments"""
    assignments = SubjectAssignment.objects.all().order_by("-term__session__start_date")
    current_term = Term.objects.filter(is_current=True).first()

    if current_term:
        assignments = assignments.filter(term=current_term)

    return render(
        request,
        "academics/assignment_list.html",
        {"assignments": assignments, "current_term": current_term},
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def assignment_create(request):
    """Create subject assignment"""
    if request.method == "POST":
        form = SubjectAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            messages.success(request, "Subject assigned successfully!")
            return redirect("academics:assignment_list")
    else:
        form = SubjectAssignmentForm()

    return render(
        request, "academics/assignment_form.html", {"form": form, "action": "Create"}
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def assignment_update(request, pk):
    """Update subject assignment"""
    assignment = get_object_or_404(SubjectAssignment, pk=pk)

    if request.method == "POST":
        form = SubjectAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment updated successfully!")
            return redirect("academics:assignment_list")
    else:
        form = SubjectAssignmentForm(instance=assignment)

    return render(
        request,
        "academics/assignment_form.html",
        {"form": form, "assignment": assignment, "action": "Update"},
    )


# ============================================
# ASSESSMENT MANAGEMENT
# ============================================


@login_required
def assessment_list(request):
    """List all assessments"""
    assessments = Assessment.objects.all().order_by("-date")

    # Filter by teacher if not superuser
    if not request.user.is_superuser:
        assessments = assessments.filter(assignment__teacher=request.user)

    # Search and filter
    query = request.GET.get("q")
    if query:
        assessments = assessments.filter(
            Q(title__icontains=query) | Q(assignment__subject__name__icontains=query)
        )

    # Pagination
    paginator = Paginator(assessments, 20)
    page = request.GET.get("page")
    assessments = paginator.get_page(page)

    return render(
        request,
        "academics/assessment_list.html",
        {"assessments": assessments, "query": query},
    )


@login_required
def assessment_create(request):
    """Create new assessment"""
    if request.method == "POST":
        form = AssessmentForm(request.POST, user=request.user)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.created_by = request.user
            assessment.save()
            messages.success(
                request, f'Assessment "{assessment.title}" created successfully!'
            )
            return redirect("academics:assessment_detail", pk=assessment.pk)
    else:
        form = AssessmentForm(user=request.user)

    return render(
        request, "academics/assessment_form.html", {"form": form, "action": "Create"}
    )


@login_required
def assessment_update(request, pk):
    """Update assessment"""
    assessment = get_object_or_404(Assessment, pk=pk)

    # Check permission
    if not request.user.is_superuser and assessment.created_by != request.user:
        messages.error(request, "You do not have permission to edit this assessment.")
        return redirect("academics:assessment_list")

    if request.method == "POST":
        form = AssessmentForm(request.POST, instance=assessment, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Assessment updated successfully!")
            return redirect("academics:assessment_detail", pk=assessment.pk)
    else:
        form = AssessmentForm(instance=assessment, user=request.user)

    return render(
        request,
        "academics/assessment_form.html",
        {"form": form, "assessment": assessment, "action": "Update"},
    )


@login_required
def assessment_detail(request, pk):
    """View assessment details with scores"""
    assessment = get_object_or_404(Assessment, pk=pk)

    # Get all scores for this assessment
    scores = StudentScore.objects.filter(assessment=assessment).select_related(
        "student"
    )

    # DEBUG: Print to console
    print(f"Assessment ID: {assessment.id}")
    print(f"Number of scores found: {scores.count()}")
    for score in scores:
        print(f"Student: {score.student.full_name}, Score: {score.score}")

    # Calculate statistics
    if scores.exists():
        stats = scores.aggregate(
            avg_score=Avg("score"),
            highest_score=Max("score"),
            lowest_score=Min("score"),
            total_students=Count("id"),
        )

        # Pass/Fail count
        pass_count = scores.filter(score__gte=(assessment.max_score * 0.4)).count()
        fail_count = scores.filter(score__lt=(assessment.max_score * 0.4)).count()

        stats["pass_count"] = pass_count
        stats["fail_count"] = fail_count
        stats["pass_rate"] = (
            (pass_count / stats["total_students"] * 100)
            if stats["total_students"] > 0
            else 0
        )
    else:
        stats = None

    context = {
        "assessment": assessment,
        "student_scores": scores,
        "stats": stats,
    }

    return render(request, "academics/assessment_detail.html", context)


@login_required
def assessment_delete(request, pk):
    """Delete assessment"""
    assessment = get_object_or_404(Assessment, pk=pk)

    # Check permission
    if not request.user.is_superuser and assessment.created_by != request.user:
        messages.error(request, "You do not have permission to delete this assessment.")
        return redirect("academics:assessment_list")

    if request.method == "POST":
        assessment_title = assessment.title
        assessment.delete()
        messages.success(
            request, f'Assessment "{assessment_title}" deleted successfully!'
        )
        return redirect("academics:assessment_list")

    return render(
        request, "academics/assessment_confirm_delete.html", {"assessment": assessment}
    )


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
@require_POST
def publish_assessment(request, pk):
    """Publish an assessment, making scores visible."""
    assessment = get_object_or_404(Assessment, pk=pk)
    assessment.is_published = True
    assessment.published_at = timezone.now()
    assessment.save(update_fields=["is_published", "published_at"])
    messages.success(request, f'Assessment "{assessment.title}" has been published.')
    return redirect("academics:assessment_detail", pk=pk)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
@require_POST
def unpublish_assessment(request, pk):
    """Unpublish an assessment, hiding scores."""
    assessment = get_object_or_404(Assessment, pk=pk)
    assessment.is_published = False
    assessment.published_at = None
    assessment.save(update_fields=["is_published", "published_at"])
    messages.info(request, f'Assessment "{assessment.title}" has been unpublished.')
    return redirect("academics:assessment_detail", pk=pk)


# ============================================
# SCORE ENTRY
# ============================================


@login_required
def bulk_score_entry(request, assessment_id):
    """Bulk score entry for students"""
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # Get students from the classroom
    try:
        students = assessment.assignment.classroom.students.all().order_by(
            "surname", "other_name"
        )
    except AttributeError:
        try:
            students = assessment.assignment.classroom.student_set.all().order_by(
                "surname", "other_name"
            )
        except AttributeError:
            students = Student.objects.filter(
                classroom=assessment.assignment.classroom
            ).order_by("surname", "other_name")

    if request.method == "POST":
        saved_count = 0
        errors = []

        for student in students:
            score_key = f"score_{student.id}"
            remarks_key = f"remarks_{student.id}"

            score_value = request.POST.get(score_key, "").strip()
            remarks_value = request.POST.get(remarks_key, "").strip()

            if score_value:
                try:
                    score_float = float(score_value)

                    if score_float < 0 or score_float > assessment.max_score:
                        errors.append(
                            f"{student.full_name}: Score must be between 0 and {assessment.max_score}"
                        )
                        continue

                    # Create or update score - let the model calculate percentage and grade
                    score_obj, created = StudentScore.objects.update_or_create(
                        assessment=assessment,
                        student=student,
                        defaults={
                            "score": score_float,
                            "remarks": remarks_value,
                            "submitted_by": request.user,
                        },
                    )
                    saved_count += 1

                except (ValueError, TypeError):
                    errors.append(f"{student.full_name}: Invalid score format")
                    continue

        if saved_count > 0:
            messages.success(request, f"✅ Successfully saved {saved_count} score(s)!")

        if errors:
            for error in errors:
                messages.error(request, error)

        if saved_count == 0 and not errors:
            messages.warning(request, "No scores were entered.")

        return redirect("academics:assessment_detail", pk=assessment_id)

    # GET request - Attach existing scores to students
    scores_qs = StudentScore.objects.filter(assessment=assessment).select_related(
        "student"
    )
    scores_dict = {score.student.id: score for score in scores_qs}

    students_with_scores = []
    for student in students:
        student.existing_score = scores_dict.get(student.id)
        students_with_scores.append(student)

    context = {
        "assessment": assessment,
        "students": students_with_scores,
    }

    return render(request, "academics/bulk_score_entry.html", context)


@login_required
def import_scores(request):
    """Import scores from Excel/CSV"""
    if request.method == "POST":
        form = ScoreImportForm(request.POST, request.FILES)
        if form.is_valid():
            assessment = form.cleaned_data["assessment"]
            file = request.FILES["file"]

            try:
                # Read file based on extension
                if file.name.endswith(".csv"):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)

                # Expected columns: admission_no, score, remarks (optional)
                success_count = 0
                error_count = 0
                errors = []

                with transaction.atomic():
                    for index, row in df.iterrows():
                        try:
                            student = Student.objects.get(
                                admission_no=row["admission_no"]
                            )

                            StudentScore.objects.update_or_create(
                                assessment=assessment,
                                student=student,
                                defaults={
                                    "score": row["score"],
                                    "remarks": row.get("remarks", ""),
                                    "submitted_by": request.user,
                                },
                            )
                            success_count += 1
                        except Student.DoesNotExist:
                            error_count += 1
                            errors.append(
                                f"Row {index + 2}: Student with admission no {row['admission_no']} not found"
                            )
                        except Exception as e:
                            error_count += 1
                            errors.append(f"Row {index + 2}: {str(e)}")

                if success_count > 0:
                    messages.success(
                        request, f"{success_count} scores imported successfully!"
                    )

                if error_count > 0:
                    messages.warning(
                        request,
                        f"{error_count} rows had errors. Check the details below.",
                    )
                    for error in errors[:10]:  # Show first 10 errors
                        messages.error(request, error)

                return redirect("academics:assessment_detail", pk=assessment.id)

            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
    else:
        form = ScoreImportForm()

    return render(request, "academics/import_scores.html", {"form": form})


# ============================================
# REPORT CARDS
# ============================================


@login_required
def report_card_list(request):
    """List all report cards"""
    report_cards = ReportCard.objects.all().order_by(
        "-term__session__start_date", "student__surname"
    )

    # Filter options
    term_id = request.GET.get("term")
    classroom_id = request.GET.get("classroom")

    if term_id:
        report_cards = report_cards.filter(term_id=term_id)
    if classroom_id:
        report_cards = report_cards.filter(classroom_id=classroom_id)

    # Pagination
    paginator = Paginator(report_cards, 20)
    page = request.GET.get("page")
    report_cards = paginator.get_page(page)

    context = {
        "report_cards": report_cards,
        "terms": Term.objects.all(),
        "classrooms": ClassRoom.objects.all(),
    }

    return render(request, "academics/report_card_list.html", context)


@login_required
def report_card_detail(request, pk):
    """View report card details"""
    report_card = get_object_or_404(ReportCard, pk=pk)

    # Get all term results for this student and term
    term_results = TermResult.objects.filter(
        student=report_card.student, term=report_card.term
    ).select_related("subject")

    context = {
        "report_card": report_card,
        "term_results": term_results,
    }

    return render(request, "academics/report_card_detail.html", context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def publish_report_card(request, pk):
    report_card = get_object_or_404(ReportCard, pk=pk)
    report_card.is_published = True
    report_card.save(update_fields=["is_published"])
    messages.success(
        request, f"Report card for {report_card.student.full_name} has been published."
    )
    return redirect(
        request.META.get("HTTP_REFERER", reverse("academics:report_card_list"))
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def unpublish_report_card(request, pk):
    report_card = get_object_or_404(ReportCard, pk=pk)
    report_card.is_published = False
    report_card.save(update_fields=["is_published"])
    messages.info(
        request,
        f"Report card for {report_card.student.full_name} has been unpublished.",
    )
    return redirect(
        request.META.get("HTTP_REFERER", reverse("academics:report_card_list"))
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def generate_single_report_card(request):
    """Generate or refresh a single student's report card for a term/class."""
    try:
        student_id = int(request.POST.get("student_id"))
        classroom_id = int(request.POST.get("classroom_id"))
    except (TypeError, ValueError):
        messages.error(request, "Invalid data. Please provide student and class.")
        return redirect(
            request.META.get("HTTP_REFERER", reverse("academics:report_card_list"))
        )

    student = get_object_or_404(Student, id=student_id)
    term_id = request.POST.get("term_id")
    if term_id:
        term = get_object_or_404(Term, id=int(term_id))
    else:
        term = Term.objects.filter(is_current=True).first()
        if not term:
            messages.error(request, "No current term found. Please select a term.")
            return redirect(
                request.META.get("HTTP_REFERER", reverse("academics:report_card_list"))
            )
    classroom = get_object_or_404(ClassRoom, id=classroom_id)

    # Ensure term results exist for this student/class/term by reusing calculate_term_results on just this class.
    # The calculation updates/creates TermResult rows; then we build the ReportCard.
    try:
        # Calculate results for this class/term
        calculate_term_results(request, term_id=term.id, classroom_id=classroom.id)
    except Exception:
        # Continue even if calculation view redirects; results likely computed
        pass

    # Aggregate averages and create/update report card
    term_results = TermResult.objects.filter(
        student=student, term=term, classroom=classroom
    )
    if not term_results.exists():
        messages.warning(request, "No term results found for this student/term/class.")
        return redirect(
            request.META.get("HTTP_REFERER", reverse("academics:report_card_list"))
        )

    average_score = term_results.aggregate(avg=Avg("total_score"))["avg"] or 0
    all_students = classroom.students.all()

    # Compute rank map within class (by average across subjects)
    averages = (
        TermResult.objects.filter(term=term, classroom=classroom)
        .values("student_id")
        .annotate(avg_score=Avg("total_score"))
        .order_by("-avg_score")
    )
    rank_map = {}
    last_score = None
    last_rank = 0
    for idx, row in enumerate(averages, 1):
        if row["avg_score"] != last_score:
            last_rank = idx
            last_score = row["avg_score"]
        rank_map[row["student_id"]] = last_rank

    report_card, _ = ReportCard.objects.update_or_create(
        student=student,
        term=term,
        classroom=classroom,
        defaults={
            "average_score": average_score,
            "position": rank_map.get(student.id, 0),
            "out_of": all_students.count(),
        },
    )
    messages.success(request, f"Report card generated for {student.full_name}.")
    return redirect("academics:report_card_detail", pk=report_card.pk)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def generate_report_cards(request):
    """Generate report cards for multiple students"""
    if request.method == "POST":
        form = BulkReportCardGenerationForm(request.POST)
        if form.is_valid():
            term = form.cleaned_data["term"]
            classroom = form.cleaned_data["classroom"]

            # Get all students in the class
            students = classroom.students.all()
            generated_count = 0
            errors = []

            # --- Start of new ranking logic ---
            # First, calculate all student averages for the term
            student_averages = []
            for student in students:
                avg = TermResult.objects.filter(student=student, term=term).aggregate(
                    avg_score=Avg("total_score")
                )["avg_score"]
                if avg is not None:
                    student_averages.append({"student_id": student.id, "average": avg})

            # Sort students by average score in descending order
            sorted_students = sorted(
                student_averages, key=lambda x: x["average"], reverse=True
            )

            # Build a rank map that handles ties
            rank_map = {}
            last_score = -1
            last_rank = 0
            for i, data in enumerate(sorted_students, 1):
                if data["average"] != last_score:
                    last_rank = i
                    last_score = data["average"]
                rank_map[data["student_id"]] = last_rank
            # --- End of new ranking logic ---

            with transaction.atomic():
                for student in students:
                    # --- Collect individualized data from POST ---
                    class_teacher_remarks = request.POST.get(
                        f"remarks_{student.id}", ""
                    )
                    principal_remarks = request.POST.get(
                        f"principal_remarks_{student.id}", ""
                    )
                    days_present = request.POST.get(f"days_present_{student.id}")
                    days_absent = request.POST.get(f"days_absent_{student.id}")

                    # Collect domain skills
                    skill_fields = {
                        "punctuality": request.POST.get(f"punctuality_{student.id}", 0),
                        "attendance_in_class": request.POST.get(
                            f"attendance_in_class_{student.id}", 0
                        ),
                        "honesty": request.POST.get(f"honesty_{student.id}", 0),
                        "neatness": request.POST.get(f"neatness_{student.id}", 0),
                        "handwriting": request.POST.get(f"handwriting_{student.id}", 0),
                        "sports_and_games": request.POST.get(
                            f"sports_and_games_{student.id}", 0
                        ),
                    }

                    # Get all term results for this student
                    term_results = TermResult.objects.filter(
                        student=student, term=term, classroom=classroom
                    )

                    if term_results.exists():
                        # Calculate overall stats
                        average_score = (
                            term_results.aggregate(avg=Avg("total_score"))["avg"] or 0
                        )

                        # Create or update report card
                        report_card, created = ReportCard.objects.update_or_create(
                            student=student,
                            term=term,
                            classroom=classroom,
                            defaults={
                                "average_score": average_score,
                                "position": rank_map.get(student.id, 0),
                                "out_of": all_students.count(),
                                "class_teacher_remarks": class_teacher_remarks,
                                "principal_remarks": principal_remarks,
                            },
                        )
                        generated_count += 1

            messages.success(
                request, f"{generated_count} report cards generated successfully!"
            )
            return redirect("academics:report_card_list")
    else:
        form = BulkReportCardGenerationForm()

    return render(request, "academics/generate_report_cards.html", {"form": form})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def prepare_report_cards(request):
    """
    A new, interactive page for preparing report card data like remarks and skills
    before final generation.
    """
    form = BulkReportCardGenerationForm(request.GET or None)
    students = []
    classroom = None
    term = None

    if form.is_valid():
        classroom = form.cleaned_data["classroom"]
        term = form.cleaned_data["term"]

        # Get all students and pre-fetch their existing report cards to populate the form
        students_qs = classroom.students.all().order_by("surname", "other_name")
        existing_reports = ReportCard.objects.filter(
            classroom=classroom, term=term
        ).in_bulk(field_name="student_id")

        for student in students_qs:
            student.existing_report = existing_reports.get(student.id)
            students.append(student)

    context = {
        "form": form,
        "classroom": classroom,
        "term": term,
        "students": students,
        "skill_choices": ReportCard.SKILL_RATING_CHOICES,
    }
    return render(request, "academics/prepare_report_cards.html", context)


@login_required
@require_POST
def ajax_save_report_card_data(request):
    """
    Save remarks, attendance, and skills for a single student's report card via AJAX.
    This creates a placeholder report card or updates an existing one.
    """
    try:
        data = json.loads(request.body)
        student_id = data.get("student_id")
        term_id = data.get("term_id")
        classroom_id = data.get("classroom_id")

        student = get_object_or_404(Student, id=student_id)
        term = get_object_or_404(Term, id=term_id)
        classroom = get_object_or_404(ClassRoom, id=classroom_id)

        # Create or update the report card with the preparatory data
        report_card, created = ReportCard.objects.update_or_create(
            student=student,
            term=term,
            classroom=classroom,
            defaults={
                "class_teacher_remarks": data.get("class_teacher_remarks", ""),
                "principal_remarks": data.get("principal_remarks", ""),
                "days_present": data.get("days_present") or 0,
                "days_absent": data.get("days_absent") or 0,
                "punctuality": data.get("punctuality", 0),
                "attendance_in_class": data.get("attendance_in_class", 0),
                "honesty": data.get("honesty", 0),
                "neatness": data.get("neatness", 0),
                "handwriting": data.get("handwriting", 0),
                "sports_and_games": data.get("sports_and_games", 0),
            },
        )
        return JsonResponse(
            {"status": "success", "message": f"Data for {student.full_name} saved."}
        )

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
@require_POST
def finalize_report_cards(request):
    """
    Finalizes the report cards for a class by calculating averages and ranks.
    This should be called after all preparatory data has been entered.
    """
    term_id = request.POST.get("term_id")
    classroom_id = request.POST.get("classroom_id")

    term = get_object_or_404(Term, id=term_id)
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    students = classroom.students.all()

    # --- Ranking Logic ---
    averages = (
        TermResult.objects.filter(term=term, classroom=classroom)
        .values("student_id")
        .annotate(avg_score=Avg("total_score"))
        .order_by("-avg_score")
    )

    rank_map = {row["student_id"]: i + 1 for i, row in enumerate(averages)}

    # --- Update Report Cards with Final Data ---
    updated_count = 0
    with transaction.atomic():
        for student in students:
            term_results = TermResult.objects.filter(
                student=student, term=term, classroom=classroom
            )
            if term_results.exists():
                total_score = (
                    term_results.aggregate(total=Sum("total_score"))["total"] or 0
                )
                average_score = (
                    term_results.aggregate(avg=Avg("total_score"))["avg"] or 0
                )

                ReportCard.objects.filter(
                    student=student, term=term, classroom=classroom
                ).update(
                    total_score=total_score,
                    average_score=average_score,
                    position=rank_map.get(student.id, 0),
                    out_of=students.count(),
                )
                updated_count += 1

    messages.success(
        request,
        f"Successfully finalized and generated {updated_count} report cards for {classroom}.",
    )
    return redirect("academics:report_card_list")


# ============================================
# ANALYTICS & REPORTS
# ============================================


class PerformanceAnalyticsView(TemplateView):
    template_name = "academics/performance_analytics.html"

    def get_queryset(self, form):
        """Build filtered queryset based on form data"""
        queryset = TermResult.objects.select_related(
            "student", "classroom", "subject", "term", "term__session"
        )

        # If no filters provided or form invalid, prefer showing current term by default
        if (
            not form.is_bound
            or not form.is_valid()
            or not any(self.request.GET.values())
        ):
            current_term = Term.objects.filter(is_current=True).first()
            if current_term:
                return queryset.filter(term=current_term)
            return queryset  # Fallback to unfiltered if no current term

        # Apply filters
        session = form.cleaned_data.get("session")
        if session:
            queryset = queryset.filter(term__session=session)

        term = form.cleaned_data.get("term")
        if term:
            queryset = queryset.filter(term=term)

        classroom = form.cleaned_data.get("classroom")
        if classroom:
            queryset = queryset.filter(classroom=classroom)

        subject = form.cleaned_data.get("subject")
        if subject:
            queryset = queryset.filter(subject=subject)

        student = form.cleaned_data.get("student")
        if student:
            queryset = queryset.filter(student=student)

        # Apply score range filters
        min_score = form.cleaned_data.get("min_score")
        max_score = form.cleaned_data.get("max_score")

        if min_score is not None:
            queryset = queryset.filter(total_score__gte=min_score)

        if max_score is not None:
            queryset = queryset.filter(total_score__lte=max_score)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Initialize form with GET data
        form = PerformanceFilterForm(self.request.GET or None)
        context["form"] = form

        # Get filtered queryset
        queryset = self.get_queryset(form)

        # Flag when we defaulted to current term (no GET filters provided)
        context["used_default_filters"] = not (
            self.request.GET and any(self.request.GET.values())
        )
        context["current_term"] = Term.objects.filter(is_current=True).first()

        # Calculate statistics
        stats = queryset.aggregate(
            avg_score=Avg("total_score"),
            highest_score=Max("total_score"),
            lowest_score=Min("total_score"),
            total_students=Count("student", distinct=True),
        )

        # Handle None values in stats
        context["stats"] = {
            "avg_score": stats["avg_score"] or 0,
            "highest_score": stats["highest_score"] or 0,
            "lowest_score": stats["lowest_score"] or 0,
            "total_students": stats["total_students"] or 0,
        }

        # Subject Performance
        subject_performance = (
            queryset.values("subject__name")
            .annotate(
                avg_score=Avg("total_score"),
                student_count=Count("student", distinct=True),
            )
            .order_by("-avg_score")
        )
        context["subject_performance"] = subject_performance

        # Class Performance
        class_performance = (
            queryset.values("classroom__level", "classroom__arm")
            .annotate(avg_score=Avg("total_score"))
            .order_by("classroom__level", "classroom__arm")
        )
        context["class_performance"] = class_performance

        # Grade Distribution (customize these ranges based on your grading system)
        grade_distribution = {
            "A": queryset.filter(total_score__gte=70).count(),
            "B": queryset.filter(total_score__gte=60, total_score__lt=70).count(),
            "C": queryset.filter(total_score__gte=50, total_score__lt=60).count(),
            "D": queryset.filter(total_score__gte=45, total_score__lt=50).count(),
            "E": queryset.filter(total_score__gte=40, total_score__lt=45).count(),
            "F": queryset.filter(total_score__lt=40).count(),
        }
        context["grade_distribution"] = grade_distribution

        # Pass/Fail Statistics (assuming 40 is pass mark)
        pass_fail_stats = {
            "pass_count": queryset.filter(total_score__gte=40).count(),
            "fail_count": queryset.filter(total_score__lt=40).count(),
        }
        context["pass_fail_stats"] = pass_fail_stats

        # Performance Trend Over Time
        performance_trend = list(
            queryset.values("term__name", "term__id")
            .annotate(avg_score=Avg("total_score"))
            .order_by("term__id")
        )

        # Convert Decimal to float for JSON serialization
        for item in performance_trend:
            if item.get("avg_score"):
                item["avg_score"] = float(item["avg_score"])

        context["performance_trend"] = json.dumps(performance_trend)

        # Top 10 Performers - Better approach
        top_performers_qs = (
            queryset.values(
                "student__id",
                "student__surname",
                "student__other_name",
                "classroom__level",
                "classroom__arm",
            )
            .annotate(total_score=Avg("total_score"))
            .order_by("-total_score")[:10]
        )

        # Format the data properly
        top_performers = []
        for performer in top_performers_qs:
            # Create a simple object to match template expectations
            class StudentObj:
                def __init__(self, surname, other_name):
                    self.full_name = f"{surname} {other_name}"

            top_performers.append(
                {
                    "student": StudentObj(
                        performer["student__surname"], performer["student__other_name"]
                    ),
                    "classroom": f"{performer['classroom__level']}{performer['classroom__arm']}",
                    "average_score": float(performer["total_score"] or 0),
                }
            )

        context["top_performers"] = top_performers

        return context


# ============================================
# AJAX/API VIEWS
# ============================================


@login_required
@require_POST
def ajax_save_score(request):
    """Save a single student score via AJAX."""
    try:
        import json

        data = json.loads(request.body)

        assessment_id = data.get("assessment_id")
        student_id = data.get("student_id")
        score_val = data.get("score")
        remarks = data.get("remarks", "")

        assessment = get_object_or_404(Assessment, id=assessment_id)

        # Permission check
        if (
            not request.user.is_superuser
            and assessment.assignment.teacher != request.user
        ):
            return JsonResponse(
                {"status": "error", "message": "Permission denied."}, status=403
            )

        student = get_object_or_404(Student, id=student_id)

        # Validate score
        if score_val is None or score_val == "":
            # If score is cleared, delete the entry
            StudentScore.objects.filter(assessment=assessment, student=student).delete()
            return JsonResponse({"status": "success", "message": "Score cleared."})

        score = float(score_val)
        if not (0 <= score <= assessment.max_score):
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Score must be between 0 and {assessment.max_score}.",
                },
                status=400,
            )

        # Update or create the score
        StudentScore.objects.update_or_create(
            assessment=assessment,
            student=student,
            defaults={
                "score": score,
                "remarks": remarks,
                "submitted_by": request.user,
            },
        )

        return JsonResponse({"status": "success", "message": "Score saved."})

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
def get_subjects_by_class(request):
    """Get subjects for a specific class (AJAX)"""
    classroom_id = request.GET.get("classroom_id")
    term_id = request.GET.get("term_id")

    assignments = SubjectAssignment.objects.filter(
        classroom_id=classroom_id, term_id=term_id
    ).select_related("subject")

    subjects = [{"id": a.subject.id, "name": a.subject.name} for a in assignments]

    return JsonResponse({"subjects": subjects})


@login_required
def get_students_by_class(request):
    """Get students for a specific class (AJAX)"""
    classroom_id = request.GET.get("classroom_id")

    students = Student.objects.filter(classroom_id=classroom_id).values(
        "id",
        "surname",
        "other_name",
        "admission_no",
        "classroom__level",
        "classroom__arm",
    )

    student_list = [
        {
            "id": s["id"],
            "name": f"{s['surname']} {s['other_name']}",
            "admission_no": s["admission_no"],
            "class": f"{s['classroom__level']}{s['classroom__arm']}",
        }
        for s in students
    ]

    return JsonResponse({"students": student_list})


# ============================================
# EXCEL EXPORT VIEWS
# ============================================


@login_required
def export_assessment_template(request, assessment_id):
    """Export Excel template for score entry"""
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # Get students in the class
    students = assessment.assignment.classroom.students.all().order_by(
        "surname", "other_name"
    )

    # Create DataFrame
    data = {
        "Admission No": [s.admission_no for s in students],
        "Student Name": [s.full_name for s in students],
        "Class": [str(s.classroom) for s in students],
        "Score": [""] * len(students),
        "Remarks": [""] * len(students),
    }

    df = pd.DataFrame(data)

    # Create Excel file
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{assessment.title}_template.xlsx"'
    )

    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Scores")

        # Auto-adjust column widths
        worksheet = writer.sheets["Scores"]
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).apply(len).max(), len(col))
            worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

    return response


@login_required
def export_class_results(request, classroom_id, term_id):
    """Export class results to Excel"""
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    term = get_object_or_404(Term, id=term_id)

    # Get all term results for this class and term
    results = (
        TermResult.objects.filter(classroom=classroom, term=term)
        .select_related("student", "subject")
        .order_by("student__surname", "subject__name")
    )

    # Create DataFrame
    data = []
    for result in results:
        data.append(
            {
                "Admission No": result.student.admission_no,
                "Student Name": result.student.full_name,
                "Subject": result.subject.name,
                "CA Total": result.ca_total,
                "Exam Score": result.exam_score,
                "Total Score": result.total_score,
                "Grade": result.grade,
                "Position": result.position,
                "Class Average": result.class_average,
                "Remarks": result.teacher_remarks,
            }
        )

    df = pd.DataFrame(data)

    # Create Excel file
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{classroom}_{term}_results.xlsx"'
    )

    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")

    return response


# ============================================
# CSV EXPORT FOR ANALYTICS
# ============================================


@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_subject_performance_csv(request):
    """Export subject performance table (based on current filters) to CSV."""
    form = PerformanceFilterForm(request.GET or None)
    view = PerformanceAnalyticsView()
    view.request = request
    queryset = view.get_queryset(form)

    subject_performance = (
        queryset.values("subject__name")
        .annotate(
            avg_score=Avg("total_score"), student_count=Count("student", distinct=True)
        )
        .order_by("-avg_score")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="subject_performance.csv"'

    writer = csv.writer(response)
    writer.writerow(["Subject", "Average Score", "Students"])
    for row in subject_performance:
        writer.writerow(
            [row["subject__name"], float(row["avg_score"] or 0), row["student_count"]]
        )

    return response


@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_class_performance_csv(request):
    """Export class performance table (based on current filters) to CSV."""
    form = PerformanceFilterForm(request.GET or None)
    view = PerformanceAnalyticsView()
    view.request = request
    queryset = view.get_queryset(form)

    class_performance = (
        queryset.values("classroom__level", "classroom__arm")
        .annotate(avg_score=Avg("total_score"))
        .order_by("classroom__level", "classroom__arm")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="class_performance.csv"'

    writer = csv.writer(response)
    writer.writerow(["Class", "Average Score"])
    for row in class_performance:
        class_name = f"{row['classroom__level']}{row['classroom__arm']}"
        writer.writerow([class_name, float(row["avg_score"] or 0)])

    return response


# ============================================
# RECALCULATE TERM RESULTS (ACTION)
# ============================================


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def recalculate_term_results(request):
    """Recalculate term results for a selected class and term, then redirect back to analytics."""
    term_id = request.POST.get("term_id")
    classroom_id = request.POST.get("classroom_id")
    if not term_id or not classroom_id:
        messages.error(
            request, "Please select both term and class to recalculate results."
        )
        return redirect(
            f"{reverse('academics:performance_analytics')}?{request.META.get('QUERY_STRING', '')}"
        )

    # Call existing calculation logic
    try:
        # Reuse calculate_term_results view logic by calling it directly
        return calculate_term_results(
            request, term_id=int(term_id), classroom_id=int(classroom_id)
        )
    except Exception as e:
        messages.error(request, f"Failed to recalculate results: {e}")
        return redirect(
            f"{reverse('academics:performance_analytics')}?{request.META.get('QUERY_STRING', '')}"
        )


@login_required
def export_report_cards(request, term_id):
    """Export all report cards for a term"""
    term = get_object_or_404(Term, id=term_id)

    report_cards = ReportCard.objects.filter(term=term).select_related(
        "student", "classroom"
    )

    data = []
    for rc in report_cards:
        data.append(
            {
                "Admission No": rc.student.admission_no,
                "Student Name": rc.student.full_name,
                "Class": str(rc.classroom),
                "Total Score": rc.total_score,
                "Average Score": rc.average_score,
                "Position": f"{rc.position}/{rc.out_of}",
                "Days Present": rc.days_present,
                "Days Absent": rc.days_absent,
                "Class Teacher Remarks": rc.class_teacher_remarks,
                "Principal Remarks": rc.principal_remarks,
            }
        )

    df = pd.DataFrame(data)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{term}_report_cards.xlsx"'

    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Report Cards")

    return response


# ============================================
# PDF REPORT CARD GENERATION
# ============================================


@login_required
def generate_report_card_pdf(request, pk):
    """Generate PDF report card"""
    from django.template.loader import render_to_string
    from weasyprint import HTML
    import tempfile

    report_card = get_object_or_404(ReportCard, pk=pk)

    # Get all term results
    term_results = (
        TermResult.objects.filter(student=report_card.student, term=report_card.term)
        .select_related("subject")
        .order_by("subject__name")
    )

    # Render HTML
    html_string = render_to_string(
        "academics/report_card_pdf.html",
        {
            "report_card": report_card,
            "term_results": term_results,
        },
    )

    # Generate PDF
    html = HTML(string=html_string)
    result = html.write_pdf()

    # Create response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="report_card_{report_card.student.admission_no}_{report_card.term}.pdf"'
    )
    response.write(result)

    return response


# ============================================
# ASSESSMENT TYPE MANAGEMENT
# ============================================


@login_required
@user_passes_test(lambda u: u.is_superuser)
def assessment_type_list(request):
    """List all assessment types"""
    assessment_types = AssessmentType.objects.all().order_by("weight")
    return render(
        request,
        "academics/assessment_type_list.html",
        {"assessment_types": assessment_types},
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def assessment_type_create(request):
    """Create assessment type"""
    if request.method == "POST":
        form = AssessmentTypeForm(request.POST)
        if form.is_valid():
            assessment_type = form.save()
            messages.success(
                request,
                f'Assessment type "{assessment_type.name}" created successfully!',
            )
            return redirect("academics:assessment_type_list")
    else:
        form = AssessmentTypeForm()

    return render(
        request,
        "academics/assessment_type_form.html",
        {"form": form, "action": "Create"},
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def assessment_type_update(request, pk):
    """Update assessment type"""
    assessment_type = get_object_or_404(AssessmentType, pk=pk)

    if request.method == "POST":
        form = AssessmentTypeForm(request.POST, instance=assessment_type)
        if form.is_valid():
            form.save()
            messages.success(request, "Assessment type updated successfully!")
            return redirect("academics:assessment_type_list")
    else:
        form = AssessmentTypeForm(instance=assessment_type)

    return render(
        request,
        "academics/assessment_type_form.html",
        {"form": form, "assessment_type": assessment_type, "action": "Update"},
    )


# ============================================
# TERM RESULT CALCULATION
# ============================================


@login_required
def calculate_term_results(request, term_id, classroom_id):
    """Calculate and save term results for a class"""
    term = get_object_or_404(Term, id=term_id)
    classroom = get_object_or_404(ClassRoom, id=classroom_id)

    # Get all subject assignments for this class and term
    assignments = SubjectAssignment.objects.filter(classroom=classroom, term=term)

    # Get all students in this class
    students = classroom.students.all()

    results_created = 0

    with transaction.atomic():
        for assignment in assignments:
            for student in students:
                # Get all assessments for this subject
                assessments = Assessment.objects.filter(assignment=assignment)

                # Calculate CA total (all non-exam assessments)
                ca_scores = StudentScore.objects.filter(
                    assessment__in=assessments.exclude(assessment_type__code="EXAM"),
                    student=student,
                )

                ca_total = sum(
                    (score.score / score.assessment.max_score)
                    * score.assessment.assessment_type.weight
                    for score in ca_scores
                )

                # Get exam score
                exam_assessment = assessments.filter(
                    assessment_type__code="EXAM"
                ).first()
                exam_score = 0

                if exam_assessment:
                    exam_score_obj = StudentScore.objects.filter(
                        assessment=exam_assessment, student=student
                    ).first()

                    if exam_score_obj:
                        exam_score = (
                            exam_score_obj.score / exam_assessment.max_score
                        ) * 60

                # Create or update term result
                term_result, created = TermResult.objects.update_or_create(
                    student=student,
                    subject=assignment.subject,
                    term=term,
                    classroom=classroom,
                    defaults={
                        "ca_total": ca_total,
                        "exam_score": exam_score,
                    },
                )

                if created:
                    results_created += 1

        # Calculate class statistics for each subject
        for assignment in assignments:
            subject_results = TermResult.objects.filter(
                subject=assignment.subject, term=term, classroom=classroom
            )

            if subject_results.exists():
                stats = subject_results.aggregate(
                    avg=Avg("total_score"),
                    max_score=Max("total_score"),
                    min_score=Min("total_score"),
                )

                # Update each result with class stats
                subject_results.update(
                    class_average=stats["avg"],
                    highest_score=stats["max_score"],
                    lowest_score=stats["min_score"],
                )

                # Calculate positions
                sorted_results = subject_results.order_by("-total_score")
                for position, result in enumerate(sorted_results, start=1):
                    result.position = position
                    result.save(update_fields=["position"])

    messages.success(
        request, f"{results_created} term results calculated successfully!"
    )
    return redirect("academics:classroom_detail", pk=classroom_id)


# ============================================
# PERFORMANCE COMMENTS
# ============================================


@login_required
@user_passes_test(lambda u: u.is_superuser)
def comment_list(request):
    """List all performance comments"""
    comments = PerformanceComment.objects.filter(is_active=True).order_by("category")
    return render(request, "academics/comment_list.html", {"comments": comments})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def comment_create(request):
    """Create performance comment"""
    if request.method == "POST":
        form = PerformanceCommentForm(request.POST)
        if form.is_valid():
            comment = form.save()
            messages.success(request, "Comment created successfully!")
            return redirect("academics:comment_list")
    else:
        form = PerformanceCommentForm()

    return render(
        request, "academics/comment_form.html", {"form": form, "action": "Create"}
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def comment_update(request, pk):
    """Update performance comment"""
    comment = get_object_or_404(PerformanceComment, pk=pk)

    if request.method == "POST":
        form = PerformanceCommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, "Comment updated successfully!")
            return redirect("academics:comment_list")
    else:
        form = PerformanceCommentForm(instance=comment)

    return render(
        request,
        "academics/comment_form.html",
        {"form": form, "comment": comment, "action": "Update"},
    )


# ============================================
# STUDENT PERFORMANCE VIEW
# ============================================


@login_required
def student_performance(request, student_id):
    """View individual student performance across terms"""
    student = get_object_or_404(Student, id=student_id)

    # Get all term results for this student
    term_results = (
        TermResult.objects.filter(student=student)
        .select_related("subject", "term", "classroom")
        .order_by("-term__session__start_date", "subject__name")
    )

    # Get all report cards
    report_cards = ReportCard.objects.filter(student=student).order_by(
        "-term__session__start_date"
    )

    # Calculate overall statistics
    if term_results.exists():
        stats = term_results.aggregate(
            overall_avg=Avg("total_score"),
            best_score=Max("total_score"),
            lowest_score=Min("total_score"),
        )

        # Subject-wise average
        subject_averages = (
            term_results.values("subject__name")
            .annotate(avg_score=Avg("total_score"))
            .order_by("-avg_score")
        )
    else:
        stats = None
        subject_averages = None

    context = {
        "student": student,
        "term_results": term_results,
        "report_cards": report_cards,
        "stats": stats,
        "subject_averages": subject_averages,
    }

    return render(request, "academics/student_performance.html", context)


# ============================================
# TIMETABLE MANAGEMENT
# ============================================


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def timetable_list(request):
    """List all timetable entries."""
    timetables = (
        Timetable.objects.all()
        .select_related("classroom", "subject", "teacher", "term")
        .order_by(
            "term__session__start_date",
            "classroom__level",
            "day_of_week",
            "period_number",
        )
    )

    # Filter options
    classroom_id = request.GET.get("classroom")
    term_id = request.GET.get("term")
    day_of_week = request.GET.get("day_of_week")

    if classroom_id:
        timetables = timetables.filter(classroom_id=classroom_id)
    if term_id:
        timetables = timetables.filter(term_id=term_id)
    if day_of_week:
        timetables = timetables.filter(day_of_week=day_of_week)

    context = {
        "timetables": timetables,
        "classrooms": ClassRoom.objects.filter(session__is_current=True).order_by(
            "level", "arm"
        ),
        "terms": Term.objects.all().order_by("-session__start_date", "name"),
        "days_of_week": Timetable.DAYS_OF_WEEK,
        "selected_classroom_id": int(classroom_id) if classroom_id else None,
        "selected_term_id": int(term_id) if term_id else None,
        "selected_day_of_week": day_of_week,
    }
    return render(request, "academics/timetable_list.html", context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def timetable_create(request):
    """Create a new timetable entry."""
    if request.method == "POST":
        form = TimetableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Timetable entry created successfully!")
            return redirect("academics:timetable_list")
    else:
        form = TimetableForm()
    return render(
        request, "academics/timetable_form.html", {"form": form, "action": "Create"}
    )


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def timetable_update(request, pk):
    """Update an existing timetable entry."""
    timetable = get_object_or_404(Timetable, pk=pk)
    if request.method == "POST":
        form = TimetableForm(request.POST, instance=timetable)
        if form.is_valid():
            form.save()
            messages.success(request, "Timetable entry updated successfully!")
            return redirect("academics:timetable_list")
    else:
        form = TimetableForm(instance=timetable)
    return render(
        request,
        "academics/timetable_form.html",
        {"form": form, "timetable": timetable, "action": "Update"},
    )


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def timetable_delete(request, pk):
    """Delete a timetable entry."""
    timetable = get_object_or_404(Timetable, pk=pk)
    if request.method == "POST":
        timetable.delete()
        messages.success(request, "Timetable entry deleted successfully!")
        return redirect("academics:timetable_list")
    return render(
        request, "academics/timetable_confirm_delete.html", {"timetable": timetable}
    )


# ============================================
# TEACHER PERFORMANCE VIEW
# ============================================


@login_required
def teacher_performance(request):
    """View teacher's class performance"""
    # Get teacher's assignments
    assignments = SubjectAssignment.objects.filter(
        teacher=request.user, term__is_current=True
    )

    performance_data = []

    for assignment in assignments:
        # Get all term results for this assignment
        results = TermResult.objects.filter(
            subject=assignment.subject,
            term=assignment.term,
            classroom=assignment.classroom,
        )

        if results.exists():
            stats = results.aggregate(
                avg_score=Avg("total_score"),
                pass_count=Count("id", filter=Q(total_score__gte=40)),
                total_students=Count("id"),
            )

            stats["pass_rate"] = (
                (stats["pass_count"] / stats["total_students"] * 100)
                if stats["total_students"] > 0
                else 0
            )

            performance_data.append({"assignment": assignment, "stats": stats})

    context = {
        "assignments": assignments,
        "performance_data": performance_data,
    }

    return render(request, "academics/teacher_performance.html", context)


@login_required
def take_attendance(request):
    """View for taking daily attendance for a class."""
    selected_classroom = None
    students = []
    records_exist_for_date = False
    attendance_date = timezone.now().date()

    # Handle form submission for saving attendance
    if request.method == "POST":
        classroom_id = request.POST.get("classroom_id")
        date_str = request.POST.get("date")
        classroom = get_object_or_404(ClassRoom, id=classroom_id)
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        with transaction.atomic():
            for student in classroom.students.all():
                status = request.POST.get(f"status_{student.id}")
                remarks = request.POST.get(f"remarks_{student.id}", "")

                if status:
                    Attendance.objects.update_or_create(
                        student=student,
                        date=date,
                        defaults={
                            "status": status,
                            "remarks": remarks,
                            "marked_by": request.user,
                        },
                    )
        messages.success(
            request, f"Attendance for {classroom} on {date} saved successfully."
        )
        return redirect(
            f"{reverse('academics:take_attendance')}?classroom={classroom_id}&date={date_str}"
        )

    # Handle GET request to display students
    classroom_id = request.GET.get("classroom")
    date_str = request.GET.get("date")

    if date_str:
        attendance_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    if classroom_id:
        selected_classroom = get_object_or_404(ClassRoom, id=classroom_id)
        students = selected_classroom.students.all().order_by("surname", "other_name")

        # Attach existing attendance records for the selected date
        # Use a dictionary comprehension instead of in_bulk for non-unique fields
        existing_records_qs = Attendance.objects.filter(
            student__in=students, date=attendance_date
        )
        existing_records = {record.student_id: record for record in existing_records_qs}

        if existing_records:
            records_exist_for_date = True

        for student in students:
            student.existing_record = existing_records.get(student.id)

    context = {
        "classrooms": ClassRoom.objects.filter(session__is_current=True),
        "selected_classroom": selected_classroom,
        "students": students,
        "attendance_date": attendance_date,
        "records_exist_for_date": records_exist_for_date,
        "attendance_statuses": Attendance.ATTENDANCE_STATUS,
    }
    return render(request, "academics/take_attendance.html", context)


@login_required
def attendance_report(request):
    """
    View for generating and displaying attendance reports for a class.
    """
    selected_classroom = None
    selected_term = None
    students_report = []
    summary_stats = {}

    # Get all terms for the dropdown
    terms = Term.objects.all().order_by("-session__start_date", "name")

    # Get filter parameters
    classroom_id = request.GET.get("classroom")
    term_id = request.GET.get("term")
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    # Set default dates to the last 7 days if not provided
    today = timezone.now().date()
    if not start_date_str:
        start_date_str = (today - timezone.timedelta(days=7)).strftime("%Y-%m-%d")
    if not end_date_str:
        end_date_str = today.strftime("%Y-%m-%d")

    if term_id:
        selected_term = get_object_or_404(Term, id=term_id)
        # If a term is selected, override start and end dates with term's dates
        start_date_str = selected_term.start_date.strftime("%Y-%m-%d")
        end_date_str = selected_term.end_date.strftime("%Y-%m-%d")

    if classroom_id:
        selected_classroom = get_object_or_404(ClassRoom, id=classroom_id)
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        students = selected_classroom.students.all().order_by("surname", "other_name")
        attendance_records = Attendance.objects.filter(
            student__in=students,
            date__range=[start_date, end_date],  # This line had the error
        ).order_by("student", "date")

        # Overall summary
        summary_stats = attendance_records.values("status").annotate(count=Count("id"))

        # Per-student summary
        for student in students:
            student_records = attendance_records.filter(student=student)
            students_report.append(
                {
                    "student": student,
                    "present": student_records.filter(status="Present").count(),
                    "absent": student_records.filter(status="Absent").count(),
                    "late": student_records.filter(status="Late").count(),
                    "excused": student_records.filter(status="Excused").count(),
                }
            )

    context = {
        "classrooms": ClassRoom.objects.filter(session__is_current=True),
        "terms": terms,
        "selected_term": selected_term,
        "selected_classroom": selected_classroom,
        "students_report": students_report,
        "summary_stats": {s["status"]: s["count"] for s in summary_stats},
        "start_date": start_date_str,
        "end_date": end_date_str,
    }
    return render(request, "academics/attendance_report.html", context)
