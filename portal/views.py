# portal/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from datetime import timedelta

from .models import (
    ParentProfile,
    StudentProfile,
    Announcement,
    ParentInvitation,
    PortalMessage,
    FeePayment,
    Attendance,
    Timetable,
)
from records.models import Student
from .forms import (
    UserProfileForm,
    ParentProfileForm,
    CustomPasswordChangeForm,
    PortalMessageForm,
    ParentInvitationForm,
    ReplyMessageForm,
)
from academics.models import StudentScore, TermResult, ReportCard, Term, Assessment
from academics.models import ClassRoom, SubjectAssignment


@login_required
def portal_dashboard(request):
    """
    The main entry point for the portal.
    Redirects users to their appropriate dashboard (student, parent, or staff).
    """
    user = request.user
    if hasattr(user, "parent_profile"):
        return redirect("portal:parent_dashboard")
    elif hasattr(user, "student_profile"):
        return redirect("portal:student_dashboard")
    elif user.is_staff:
        # Check if the staff user is a teacher (class teacher or subject teacher)
        is_teacher = (
            ClassRoom.objects.filter(class_teacher=user).exists()
            or SubjectAssignment.objects.filter(teacher=user).exists()
        )
        request.user.is_teacher = is_teacher  # Add flag to user object for templates
        if is_teacher:
            return redirect("portal:teacher_dashboard")
        return redirect("records:admin_dashboard")
    else:
        # For any other authenticated user without a profile
        messages.error(
            request,
            "You do not have a portal profile. Please contact an administrator.",
        )
        return redirect("accounts:login")


@login_required
def admin_impersonate_student(request, student_id):
    """
    Allows a staff user to "impersonate" a student and view their dashboard.
    """
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to do that.")
        return redirect("portal:dashboard")

    student = get_object_or_404(Student, id=student_id)
    student_profile = get_object_or_404(StudentProfile, student=student)

    #  Here, you might set a session variable to indicate impersonation
    request.session["impersonated_student_id"] = student_id

    messages.info(request, f"You are now viewing the portal as {student.full_name}.")

    # Redirect to the student dashboard
    return redirect("portal:student_dashboard")


def accept_invitation(request, token):
    """
    Allows a parent to accept an invitation and create their account.
    """
    try:
        invitation = ParentInvitation.objects.get(token=token, is_accepted=False)
    except ParentInvitation.DoesNotExist:
        messages.error(request, "This invitation is invalid or has already been used.")
        return redirect("accounts:login")

    if invitation.is_expired():
        messages.error(
            request,
            "This invitation has expired. Please contact the school for a new one.",
        )
        return redirect("accounts:login")

    if request.method == "POST":
        form = ParentInvitationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the user account
                    user = User.objects.create_user(
                        username=form.cleaned_data["username"],
                        password=form.cleaned_data["password2"],
                        email=form.cleaned_data["email"],
                        first_name=invitation.parent_name.split(" ")[0],
                        last_name=" ".join(invitation.parent_name.split(" ")[1:]),
                    )

                    # Create the parent profile
                    parent_profile = ParentProfile.objects.create(
                        user=user,
                        phone_number=invitation.parent_contact
                        if invitation.parent_contact.isdigit()
                        else None,
                        relationship="Parent",  # Or derive from student record
                    )
                    parent_profile.students.add(invitation.student)

                    # Mark invitation as accepted
                    invitation.is_accepted = True
                    invitation.accepted_at = timezone.now()
                    invitation.save()

                    messages.success(
                        request,
                        "Your account has been created successfully! You can now log in.",
                    )
                    return redirect("accounts:login")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
    else:
        form = ParentInvitationForm(
            initial={
                "email": invitation.parent_contact
                if "@" in invitation.parent_contact
                else ""
            }
        )

    return render(
        request,
        "portal/accept_invitation.html",
        {"form": form, "invitation": invitation},
    )


@login_required
@user_passes_test(lambda u: u.is_staff)
def teacher_dashboard(request):
    """
    Dashboard for teachers, showing their classes, subjects, and schedule.
    """
    teacher = request.user
    current_term = Term.objects.filter(is_current=True).first()

    # Get classes where this user is the class teacher
    homeroom_classes = ClassRoom.objects.filter(
        class_teacher=teacher, session__is_current=True
    )

    # Get all subjects this teacher is assigned to teach
    subject_assignments = (
        SubjectAssignment.objects.filter(teacher=teacher, term=current_term)
        .select_related("subject", "classroom")
        .order_by("classroom__level", "subject__name")
    )

    # Get today's timetable for the teacher
    today_str = timezone.now().strftime("%A")  # e.g., "Monday"
    todays_schedule = (
        Timetable.objects.filter(
            teacher=teacher, day_of_week=today_str, term=current_term, is_active=True
        )
        .select_related("subject", "classroom")
        .order_by("start_time")
    )

    # Get recent announcements for staff
    announcements = Announcement.objects.filter(
        Q(target_audience="All") | Q(target_audience="Staff"), is_active=True
    ).order_by("-created_at")[:5]

    # Quick stats
    # Get the unique classroom IDs from the teacher's assignments
    assigned_classroom_ids = subject_assignments.values_list(
        "classroom_id", flat=True
    ).distinct()
    # Count the distinct students in those classrooms
    total_students_taught = Student.objects.filter(
        classroom_id__in=assigned_classroom_ids
    ).count()

    context = {
        "teacher": teacher,
        "homeroom_classes": homeroom_classes,
        "subject_assignments": subject_assignments,
        "todays_schedule": todays_schedule,
        "announcements": announcements,
        "total_students_taught": total_students_taught,
        "current_term": current_term,
        "today_str": today_str,
        "attendance_report_url": reverse("academics:attendance_report"),
    }

    return render(request, "portal/teacher_dashboard.html", context)


@login_required
def parent_dashboard(request):
    """Parent dashboard view"""
    try:
        parent_profile = request.user.parent_profile
    except ParentProfile.DoesNotExist:
        messages.error(request, "Parent profile not found. Please contact admin.")
        return redirect("accounts:login")

    # Get all children
    students = parent_profile.students.all()

    # Enhance students with stats
    for student in students:
        # Get latest report card
        latest_report = (
            ReportCard.objects.filter(student=student)
            .order_by("-term__start_date")
            .first()
        )
        if latest_report:
            student.average_score = latest_report.average_score
            student.position = f"{latest_report.position}/{latest_report.out_of}"
        else:
            student.average_score = 0
            student.position = "-"

        # Calculate attendance rate
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        attendance_records = Attendance.objects.filter(
            student=student, date__gte=thirty_days_ago
        )
        if attendance_records.exists():
            present_count = attendance_records.filter(status="Present").count()
            total_days = attendance_records.count()
            student.attendance_rate = (
                (present_count / total_days * 100) if total_days > 0 else 0
            )
        else:
            student.attendance_rate = 0

    # Get announcements
    announcements = Announcement.objects.filter(
        Q(target_audience="All") | Q(target_audience="Parents"), is_active=True
    ).order_by("-created_at")[:5]

    # Get pending fees
    pending_fees = FeePayment.objects.filter(
        student__in=students, status__in=["Pending", "Partial", "Overdue"]
    ).order_by("due_date")[:5]

    # Get unread messages
    unread_messages = PortalMessage.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    # Current term
    current_term = Term.objects.filter(is_current=True).first()

    # Calculate term progress
    term_progress = 0
    if current_term:
        total_days = (current_term.end_date - current_term.start_date).days
        elapsed_days = (timezone.now().date() - current_term.start_date).days
        term_progress = (elapsed_days / total_days * 100) if total_days > 0 else 0
        term_progress = min(term_progress, 100)

    context = {
        "students": students,
        "announcements": announcements,
        "pending_fees": pending_fees,
        "unread_messages": unread_messages,
        "current_term": current_term,
        "term_progress": term_progress,
        "current_date": timezone.now(),
    }

    return render(request, "portal/parent_dashboard.html", context)


@login_required
def parent_student_detail(request, student_id):
    """View specific student details"""
    try:
        parent_profile = request.user.parent_profile
        student = get_object_or_404(Student, id=student_id, parents=parent_profile)
    except (ParentProfile.DoesNotExist, Student.DoesNotExist):
        messages.error(request, "Access denied.")
        return redirect("portal:parent_dashboard")

    # Get latest scores
    recent_scores = (
        StudentScore.objects.filter(student=student)
        .select_related("assessment")
        .order_by("-assessment__date")[:10]
    )

    # Get attendance summary
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    attendance_summary = (
        Attendance.objects.filter(student=student, date__gte=thirty_days_ago)
        .values("status")
        .annotate(count=Count("id"))
    )

    # Get latest report card
    latest_report = (
        ReportCard.objects.filter(student=student).order_by("-term__start_date").first()
    )

    context = {
        "student": student,
        "recent_scores": recent_scores,
        "attendance_summary": attendance_summary,
        "latest_report": latest_report,
    }

    return render(request, "portal/parent_student_detail.html", context)


@login_required
def parent_student_scores(request, student_id):
    """View student scores"""
    try:
        parent_profile = request.user.parent_profile
        student = get_object_or_404(Student, id=student_id, parents=parent_profile)
    except (ParentProfile.DoesNotExist, Student.DoesNotExist):
        messages.error(request, "Access denied.")
        return redirect("portal:parent_dashboard")

    # Get all scores grouped by term
    current_term = Term.objects.filter(is_current=True).first()

    scores = (
        StudentScore.objects.filter(
            student=student, assessment__assignment__term=current_term
        )
        .select_related(
            "assessment__assignment__subject", "assessment__assessment_type"
        )
        .order_by("assessment__assignment__subject", "-assessment__date")
    )

    # Group by subject
    scores_by_subject = {}
    for score in scores:
        subject_name = score.assessment.assignment.subject.name
        if subject_name not in scores_by_subject:
            scores_by_subject[subject_name] = []
        scores_by_subject[subject_name].append(score)

    context = {
        "student": student,
        "scores_by_subject": scores_by_subject,
        "current_term": current_term,
    }

    return render(request, "portal/parent_student_scores.html", context)


@login_required
def parent_student_attendance(request, student_id):
    """View student attendance"""
    try:
        parent_profile = request.user.parent_profile
        student = get_object_or_404(Student, id=student_id, parents=parent_profile)
    except (ParentProfile.DoesNotExist, Student.DoesNotExist):
        messages.error(request, "Access denied.")
        return redirect("portal:parent_dashboard")

    # Get attendance records for current term
    current_term = Term.objects.filter(is_current=True).first()

    if current_term:
        attendance_records = Attendance.objects.filter(
            student=student,
            date__gte=current_term.start_date,
            date__lte=current_term.end_date,
        ).order_by("-date")
    else:
        attendance_records = Attendance.objects.filter(student=student).order_by(
            "-date"
        )[:30]

    # Calculate statistics
    stats = attendance_records.aggregate(
        total_days=Count("id"),
        present_days=Count("id", filter=Q(status="Present")),
        absent_days=Count("id", filter=Q(status="Absent")),
        late_days=Count("id", filter=Q(status="Late")),
    )

    if stats["total_days"] > 0:
        stats["attendance_rate"] = (stats["present_days"] / stats["total_days"]) * 100
    else:
        stats["attendance_rate"] = 0

    context = {
        "student": student,
        "attendance_records": attendance_records,
        "stats": stats,
        "current_term": current_term,
    }

    return render(request, "portal/parent_student_attendance.html", context)


@login_required
def parent_student_reports(request, student_id):
    """View student report cards"""
    try:
        parent_profile = request.user.parent_profile
        student = get_object_or_404(Student, id=student_id, parents=parent_profile)
    except (ParentProfile.DoesNotExist, Student.DoesNotExist):
        messages.error(request, "Access denied.")
        return redirect("portal:parent_dashboard")

    # Get all report cards
    report_cards = ReportCard.objects.filter(
        student=student, is_published=True
    ).order_by("-term__session__start_date")

    context = {
        "student": student,
        "report_cards": report_cards,
    }

    return render(request, "portal/parent_student_reports.html", context)


@login_required
def parent_fees(request):
    """View fee payments"""
    try:
        parent_profile = request.user.parent_profile
    except ParentProfile.DoesNotExist:
        messages.error(request, "Parent profile not found.")
        return redirect("portal:parent_dashboard")

    students = parent_profile.students.all()

    # Get all fee payments
    fee_payments = FeePayment.objects.filter(student__in=students).order_by("-due_date")

    # Calculate totals
    total_due = sum(fee.amount_due for fee in fee_payments)
    total_paid = sum(fee.amount_paid for fee in fee_payments)
    total_balance = total_due - total_paid

    context = {
        "fee_payments": fee_payments,
        "total_due": total_due,
        "total_paid": total_paid,
        "total_balance": total_balance,
    }

    return render(request, "portal/parent_fees.html", context)


@login_required
def parent_timetable(request, student_id):
    """View student timetable"""
    try:
        parent_profile = request.user.parent_profile
        student = get_object_or_404(Student, id=student_id, parents=parent_profile)
    except (ParentProfile.DoesNotExist, Student.DoesNotExist):
        messages.error(request, "Access denied.")
        return redirect("portal:parent_dashboard")

    if not student.classroom:
        messages.warning(request, "Student is not assigned to a class.")
        return redirect("portal:parent_student_detail", student_id=student_id)

    current_term = Term.objects.filter(is_current=True).first()

    # Get timetable
    timetable = Timetable.objects.filter(
        classroom=student.classroom, term=current_term, is_active=True
    ).order_by("day_of_week", "period_number")

    # Organize by day
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    timetable_by_day = {day: [] for day in days}

    for entry in timetable:
        timetable_by_day[entry.day_of_week].append(entry)

    context = {
        "student": student,
        "timetable_by_day": timetable_by_day,
        "days": days,
    }

    return render(request, "portal/parent_timetable.html", context)


# ============================================
# STUDENT PORTAL VIEWS
# ============================================


@login_required
def student_dashboard(request):
    """Student dashboard view"""
    try:
        student_profile = request.user.student_profile
        student = student_profile.student
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact admin.")
        return redirect("accounts:login")

    # Get recent scores
    recent_scores = (
        StudentScore.objects.filter(student=student)
        .select_related("assessment")
        .order_by("-assessment__date")[:5]
    )

    # Get recent attendance
    recent_attendance = Attendance.objects.filter(student=student).order_by("-date")[
        :10
    ]

    # Get announcements
    announcements = Announcement.objects.filter(
        Q(target_audience="All") | Q(target_audience="Students"), is_active=True
    ).order_by("-created_at")[:5]

    # Get current term
    current_term = Term.objects.filter(is_current=True).first()

    # Get latest report card
    latest_report = (
        ReportCard.objects.filter(student=student, is_published=True)
        .order_by("-term__start_date")
        .first()
    )

    # Get unread messages
    unread_messages = PortalMessage.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    context = {
        "student": student,
        "recent_scores": recent_scores,
        "recent_attendance": recent_attendance,
        "announcements": announcements,
        "current_term": current_term,
        "latest_report": latest_report,
        "unread_messages": unread_messages,
    }

    return render(request, "portal/student_dashboard.html", context)


@login_required
def student_scores(request):
    """View student's own scores"""
    try:
        student_profile = request.user.student_profile
        student = student_profile.student
    except StudentProfile.DoesNotExist:
        messages.error(request, "Access denied.")
        return redirect("portal:student_dashboard")

    if not student_profile.can_view_scores:
        messages.error(request, "You don't have permission to view scores.")
        return redirect("portal:student_dashboard")

    current_term = Term.objects.filter(is_current=True).first()

    scores = (
        StudentScore.objects.filter(
            student=student, assessment__assignment__term=current_term
        )
        .select_related("assessment__assignment__subject")
        .order_by("assessment__assignment__subject", "-assessment__date")
    )

    # Group by subject
    scores_by_subject = {}
    for score in scores:
        subject_name = score.assessment.assignment.subject.name
        if subject_name not in scores_by_subject:
            scores_by_subject[subject_name] = []
        scores_by_subject[subject_name].append(score)

    context = {
        "student": student,
        "scores_by_subject": scores_by_subject,
        "current_term": current_term,
    }

    return render(request, "portal/student_scores.html", context)


@login_required
def student_attendance(request):
    """View student's own attendance"""
    try:
        student_profile = request.user.student_profile
        student = student_profile.student
    except StudentProfile.DoesNotExist:
        messages.error(request, "Access denied.")
        return redirect("portal:student_dashboard")

    current_term = Term.objects.filter(is_current=True).first()

    if current_term:
        attendance_records = Attendance.objects.filter(
            student=student,
            date__gte=current_term.start_date,
            date__lte=current_term.end_date,
        ).order_by("-date")
    else:
        attendance_records = Attendance.objects.filter(student=student).order_by(
            "-date"
        )[:30]

    # Calculate statistics
    stats = attendance_records.aggregate(
        total_days=Count("id"),
        present_days=Count("id", filter=Q(status="Present")),
        absent_days=Count("id", filter=Q(status="Absent")),
        late_days=Count("id", filter=Q(status="Late")),
    )

    if stats["total_days"] > 0:
        stats["attendance_rate"] = (stats["present_days"] / stats["total_days"]) * 100
    else:
        stats["attendance_rate"] = 0

    context = {
        "student": student,
        "attendance_records": attendance_records,
        "stats": stats,
        "current_term": current_term,
    }

    return render(request, "portal/student_attendance.html", context)


@login_required
def student_timetable(request):
    """View student's timetable"""
    try:
        student_profile = request.user.student_profile
        student = student_profile.student
    except StudentProfile.DoesNotExist:
        messages.error(request, "Access denied.")
        return redirect("portal:student_dashboard")

    if not student.classroom:
        messages.warning(request, "You are not assigned to a class.")
        return redirect("portal:student_dashboard")

    current_term = Term.objects.filter(is_current=True).first()

    timetable = Timetable.objects.filter(
        classroom=student.classroom, term=current_term, is_active=True
    ).order_by("day_of_week", "period_number")

    # Organize by day
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    timetable_by_day = {day: [] for day in days}

    for entry in timetable:
        timetable_by_day[entry.day_of_week].append(entry)

    context = {
        "student": student,
        "timetable_by_day": timetable_by_day,
        "days": days,
    }

    return render(request, "portal/student_timetable.html", context)


@login_required
def student_reports(request):
    """View student's report cards"""
    try:
        student_profile = request.user.student_profile
        student = student_profile.student
    except StudentProfile.DoesNotExist:
        messages.error(request, "Access denied.")
        return redirect("portal:student_dashboard")

    report_cards = ReportCard.objects.filter(
        student=student, is_published=True
    ).order_by("-term__session__start_date")

    context = {
        "student": student,
        "report_cards": report_cards,
    }

    return render(request, "portal/student_reports.html", context)


# ============================================
# ANNOUNCEMENTS
# ============================================


@login_required
def announcements_list(request):
    """List all announcements"""
    announcements = Announcement.objects.filter(is_active=True).order_by("-created_at")

    # Filter by user type
    if hasattr(request.user, "parent_profile"):
        announcements = announcements.filter(
            Q(target_audience="All") | Q(target_audience="Parents")
        )
    elif hasattr(request.user, "student_profile"):
        announcements = announcements.filter(
            Q(target_audience="All") | Q(target_audience="Students")
        )

    context = {
        "announcements": announcements,
    }

    return render(request, "portal/announcements_list.html", context)


@login_required
def announcement_detail(request, pk):
    """View announcement details"""
    announcement = get_object_or_404(Announcement, pk=pk, is_active=True)

    context = {
        "announcement": announcement,
    }

    return render(request, "portal/announcement_detail.html", context)


# ============================================
# MESSAGES
# ============================================


@login_required
def messages_inbox(request):
    """View inbox messages"""
    messages_list = PortalMessage.objects.filter(recipient=request.user).order_by(
        "-created_at"
    )

    context = {
        "messages": messages_list,
    }

    return render(request, "portal/messages_inbox.html", context)


@login_required
def compose_message(request):
    """Compose new message"""
    if request.method == "POST":
        form = PortalMessageForm(request.POST, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            # If the sender is a student, automatically set the student context
            if (
                hasattr(request.user, "student_profile")
                and "student" not in form.cleaned_data
            ):
                message.student = request.user.student_profile.student

            message.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect("portal:messages_inbox")
    else:
        form = PortalMessageForm(user=request.user)

    return render(request, "portal/compose_message.html", {"form": form})


@login_required
def reply_message(request, pk):
    """Reply to a message."""
    original_message = get_object_or_404(PortalMessage, pk=pk, recipient=request.user)
    if request.method == "POST":
        form = ReplyMessageForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.sender = request.user
            reply.recipient = original_message.sender
            reply.subject = f"Re: {original_message.subject}"
            reply.parent_message = original_message
            reply.student = original_message.student  # Carry over the student context
            reply.save()
            messages.success(request, "Your reply has been sent.")
            return redirect("portal:message_detail", pk=original_message.pk)
    else:
        form = ReplyMessageForm()

    return render(
        request,
        "portal/reply_message.html",
        {"form": form, "original_message": original_message},
    )


@login_required
def message_detail(request, pk):
    """View message details"""
    message = get_object_or_404(PortalMessage, pk=pk, recipient=request.user)

    # Mark as read
    if not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save()

    context = {
        "message": message,
    }

    return render(request, "portal/message_detail.html", context)


# ============================================
# PROFILE
# ============================================


@login_required
def portal_profile(request):
    """View profile"""
    return render(request, "portal/profile.html")


@login_required
def update_profile(request):
    """Update profile"""
    user = request.user
    user_form = UserProfileForm(instance=user)
    parent_form = None

    if hasattr(user, "parent_profile"):
        parent_form = ParentProfileForm(instance=user.parent_profile)

    if request.method == "POST":
        user_form = UserProfileForm(request.POST, instance=user)
        if hasattr(user, "parent_profile"):
            parent_form = ParentProfileForm(request.POST, instance=user.parent_profile)

        if user_form.is_valid() and (parent_form is None or parent_form.is_valid()):
            user_form.save()
            if parent_form:
                parent_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("portal:profile")
        else:
            messages.error(request, "Please correct the errors below.")

    context = {"user_form": user_form, "parent_form": parent_form}
    return render(request, "portal/update_profile.html", context)


@login_required
def change_password(request):
    """Change password"""
    if request.method == "POST":
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: Update the session to keep the user logged in
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect("portal:profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, "portal/change_password.html", {"form": form})


# c:\Users\Williams Peaceful\Portfolio\Djangoproject\Studentmanagement\portal\views.py
