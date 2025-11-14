# portal/models.py

import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from records.models import Student


class ParentProfile(models.Model):
    """Parent/Guardian profile linked to user account"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="parent_profile"
    )
    students = models.ManyToManyField(Student, related_name="parents")
    phone_number = models.CharField(max_length=20)
    relationship = models.CharField(
        max_length=50,
        choices=[
            ("Father", "Father"),
            ("Mother", "Mother"),
            ("Guardian", "Guardian"),
            ("Other", "Other"),
        ],
    )
    address = models.TextField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.relationship}"

    class Meta:
        ordering = ["user__last_name", "user__first_name"]


class StudentProfile(models.Model):
    """Student profile linked to user account for portal access"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile"
    )
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="portal_profile"
    )
    date_of_birth = models.DateField()
    can_view_scores = models.BooleanField(default=True)
    can_view_attendance = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.full_name} Portal"

    class Meta:
        ordering = ["student__surname", "student__other_name"]


class Announcement(models.Model):
    """School announcements visible in portal"""

    CATEGORY_CHOICES = [
        ("General", "General"),
        ("Academic", "Academic"),
        ("Events", "Events"),
        ("Exam", "Examination"),
        ("Holiday", "Holiday"),
        ("Emergency", "Emergency"),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default="General"
    )
    target_audience = models.CharField(
        max_length=20,
        choices=[
            ("All", "All"),
            ("Parents", "Parents Only"),
            ("Students", "Students Only"),
            ("Class", "Specific Class"),
        ],
        default="All",
    )
    target_class = models.ForeignKey(
        "academics.ClassRoom",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Only if target is 'Specific Class'",
    )
    is_urgent = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-created_at"]


class PortalMessage(models.Model):
    """Messages between parents/students and teachers/admin"""

    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="portal_messages"
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    parent_message = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.sender} to {self.recipient}"

    class Meta:
        ordering = ["-created_at"]


class FeePayment(models.Model):
    """Fee payment records"""

    PAYMENT_STATUS = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Partial", "Partial"),
        ("Overdue", "Overdue"),
    ]

    PAYMENT_TYPE = [
        ("Tuition", "Tuition Fee"),
        ("Exam", "Examination Fee"),
        ("Development", "Development Levy"),
        ("Transport", "Transport Fee"),
        ("Uniform", "Uniform"),
        ("Books", "Books"),
        ("Other", "Other"),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="fee_payments"
    )
    term = models.ForeignKey("academics.Term", on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="Pending")
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_reference = models.CharField(max_length=100, blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def balance(self):
        return self.amount_due - self.amount_paid

    def __str__(self):
        return f"{self.student.full_name} - {self.payment_type} ({self.term})"

    class Meta:
        ordering = ["-due_date"]


class Attendance(models.Model):
    """Daily attendance records"""

    ATTENDANCE_STATUS = [
        ("Present", "Present"),
        ("Absent", "Absent"),
        ("Late", "Late"),
        ("Excused", "Excused"),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="attendance_records"
    )
    date = models.DateField()
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS)
    remarks = models.TextField(blank=True) 
    marked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="portal_attendances")
    marked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"

    class Meta:
        ordering = ["-date"]
        unique_together = ["student", "date"]


class ParentInvitation(models.Model):
    """
    Represents a one-time invitation for a parent to create a portal account.
    """

    student = models.ForeignKey(
        "records.Student", on_delete=models.CASCADE, related_name="invitations"
    )
    parent_name = models.CharField(max_length=200)
    parent_contact = models.CharField(
        max_length=100, unique=True, help_text="Email or Phone Number"
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Invitation for parent of {self.student.full_name}"

    def is_expired(self):
        """Invitation expires after 7 days."""
        return timezone.now() > self.created_at + timezone.timedelta(days=7)
