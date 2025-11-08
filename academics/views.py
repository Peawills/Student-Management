# academics/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum, Max, Min
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import transaction
import pandas as pd
from datetime import datetime

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
    """View classroom details with students"""
    classroom = get_object_or_404(ClassRoom.objects.prefetch_related("students"), pk=pk)
    students = classroom.students.all().order_by("surname", "other_name")

    # Get assignments for this class
    assignments = SubjectAssignment.objects.filter(
        classroom=classroom, term__is_current=True
    )

    context = {
        "classroom": classroom,
        "students": students,
        "assignments": assignments,
    }

    return render(request, "academics/classroom_detail.html", context)


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
            from records.models import Student

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

                    percentage = (score_float / assessment.max_score) * 100

                    # Calculate grade
                    if percentage >= 80:
                        grade = "A"
                    elif percentage >= 70:
                        grade = "B"
                    elif percentage >= 60:
                        grade = "C"
                    elif percentage >= 50:
                        grade = "D"
                    elif percentage >= 40:
                        grade = "E"
                    else:
                        grade = "F"

                    score_obj, created = StudentScore.objects.update_or_create(
                        assessment=assessment,
                        student=student,
                        defaults={
                            "score": score_float,
                            "percentage": percentage,
                            "grade": grade,
                            "remarks": remarks_value,
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
def generate_report_cards(request):
    """Generate report cards for multiple students"""
    if request.method == "POST":
        form = BulkReportCardGenerationForm(request.POST)
        if form.is_valid():
            term = form.cleaned_data["term"]
            classroom = form.cleaned_data["classroom"]
            class_teacher_remarks = form.cleaned_data.get("class_teacher_remarks", "")
            principal_remarks = form.cleaned_data.get("principal_remarks", "")

            # Get all students in the class
            students = classroom.students.all()

            generated_count = 0
            with transaction.atomic():
                for student in students:
                    # Get all term results for this student
                    term_results = TermResult.objects.filter(
                        student=student, term=term, classroom=classroom
                    )

                    if term_results.exists():
                        # Calculate overall stats
                        total_score = (
                            term_results.aggregate(Sum("total_score"))[
                                "total_score__sum"
                            ]
                            or 0
                        )
                        average_score = (
                            term_results.aggregate(Avg("total_score"))[
                                "total_score__avg"
                            ]
                            or 0
                        )

                        # Calculate position (you'll need to implement ranking logic)
                        all_students = classroom.students.all()
                        # ... position calculation logic

                        # Create or update report card
                        report_card, created = ReportCard.objects.update_or_create(
                            student=student,
                            term=term,
                            classroom=classroom,
                            defaults={
                                "total_score": total_score,
                                "average_score": average_score,
                                "position": 1,  # Replace with actual calculation
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


# ============================================
# ANALYTICS & REPORTS
# ============================================


@login_required
def performance_analytics(request):
    """Performance analytics dashboard"""
    form = PerformanceFilterForm(request.GET or None)

    # Get current term
    current_term = Term.objects.filter(is_current=True).first()

    # Base queryset
    term_results = TermResult.objects.all()

    # Apply filters
    if form.is_valid():
        if form.cleaned_data.get("session"):
            term_results = term_results.filter(
                term__session=form.cleaned_data["session"]
            )
        if form.cleaned_data.get("term"):
            term_results = term_results.filter(term=form.cleaned_data["term"])
        if form.cleaned_data.get("classroom"):
            term_results = term_results.filter(classroom=form.cleaned_data["classroom"])
        if form.cleaned_data.get("subject"):
            term_results = term_results.filter(subject=form.cleaned_data["subject"])
    elif current_term:
        term_results = term_results.filter(term=current_term)

    # Calculate statistics
    stats = term_results.aggregate(
        avg_score=Avg("total_score"),
        highest_score=Max("total_score"),
        lowest_score=Min("total_score"),
        total_students=Count("student", distinct=True),
    )

    # Subject-wise performance
    subject_performance = (
        term_results.values("subject__name")
        .annotate(
            avg_score=Avg("total_score"), student_count=Count("student", distinct=True)
        )
        .order_by("-avg_score")
    )

    # Class-wise performance
    class_performance = (
        term_results.values("classroom__level", "classroom__arm")
        .annotate(
            avg_score=Avg("total_score"), student_count=Count("student", distinct=True)
        )
        .order_by("classroom__level", "classroom__arm")
    )

    # Grade distribution
    grade_distribution = {
        "A": term_results.filter(grade="A").count(),
        "B": term_results.filter(grade="B").count(),
        "C": term_results.filter(grade="C").count(),
        "D": term_results.filter(grade="D").count(),
        "E": term_results.filter(grade="E").count(),
        "F": term_results.filter(grade="F").count(),
    }

    # Top performers
    top_performers = term_results.order_by("-total_score")[:10]

    context = {
        "form": form,
        "stats": stats,
        "subject_performance": subject_performance,
        "class_performance": class_performance,
        "grade_distribution": grade_distribution,
        "top_performers": top_performers,
        "current_term": current_term,
    }

    return render(request, "academics/performance_analytics.html", context)


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
