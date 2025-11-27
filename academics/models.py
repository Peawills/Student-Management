# academics/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class AcademicSession(models.Model):
    """Academic Year/Session"""

    name = models.CharField(max_length=100)  # e.g., "2024/2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-start_date"]


class Term(models.Model):
    """School Term"""

    TERM_CHOICES = [
        ("First", "First Term"),
        ("Second", "Second Term"),
        ("Third", "Third Term"),
    ]

    session = models.ForeignKey(
        AcademicSession, on_delete=models.CASCADE, related_name="terms"
    )
    name = models.CharField(max_length=20, choices=TERM_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.session.name} - {self.name}"

    class Meta:
        unique_together = ["session", "name"]
        ordering = ["-session__start_date", "name"]


class Subject(models.Model):
    """Subject/Course"""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_core = models.BooleanField(default=True)  # Core or Elective

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class ClassRoom(models.Model):
    """Class grouping (e.g., JSS1A, SS2C)"""

    CLASS_LEVEL_CHOICES = [
        ("JSS1", "JSS 1"),
        ("JSS2", "JSS 2"),
        ("JSS3", "JSS 3"),
        ("SS1", "SS 1"),
        ("SS2", "SS 2"),
        ("SS3", "SS 3"),
    ]

    ARM_CHOICES = [
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
        ("E", "E"),
        ("F", "F"),
        ("G", "G"),
        ("H", "H"),
    ]

    level = models.CharField(max_length=10, choices=CLASS_LEVEL_CHOICES)
    arm = models.CharField(max_length=1, choices=ARM_CHOICES)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    class_teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.level}{self.arm}"

    class Meta:
        unique_together = ["level", "arm", "session"]
        ordering = ["level", "arm"]


class SubjectAssignment(models.Model):
    """Assign subjects to classes and teachers"""

    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subject_assignments"
    )
    term = models.ForeignKey(Term, on_delete=models.CASCADE)

    def __str__(self):
        return (
            f"{self.subject.name} - {self.classroom} ({self.teacher.get_full_name()})"
        )

    class Meta:
        unique_together = ["classroom", "subject", "term"]


class AssessmentType(models.Model):
    """Types of assessments (Tests, CA, Exam)"""

    name = models.CharField(max_length=100)  # Weekly Test, CA1, Mid-Term, Exam
    code = models.CharField(max_length=20, unique=True)
    weight = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    max_score = models.IntegerField(default=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.weight}%)"

    class Meta:
        ordering = ["weight"]


class Assessment(models.Model):
    """Individual assessment/test with score locking and constraints"""

    ASSESSMENT_CODE_CHOICES = [
        ("CA1", "CA 1 (0-10)"),
        ("CA2", "CA 2 (0-10)"),
        ("CA3", "CA 3 (0-10+)"),
        ("TEST", "Test (0-10)"),
        ("EXAM", "Exam (0-60)"),
    ]

    assignment = models.ForeignKey(SubjectAssignment, on_delete=models.CASCADE)
    assessment_type = models.ForeignKey(AssessmentType, on_delete=models.CASCADE)
    assessment_code = models.CharField(
        max_length=20,
        choices=ASSESSMENT_CODE_CHOICES,
        default="CA1",
        help_text="Assessment category (CA must be <=10, max CA total=40; Exam=60)",
    )
    title = models.CharField(max_length=200)
    date = models.DateField()
    max_score = models.IntegerField(default=100)
    instructions = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    # Score Locking System
    is_locked = models.BooleanField(
        default=False, help_text="When locked, scores cannot be edited"
    )
    locked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assessments_locked",
        help_text="Admin who locked the scores",
    )
    locked_at = models.DateTimeField(
        null=True, blank=True, help_text="When the scores were locked"
    )

    def clean(self):
        """Validate assessment constraints"""
        from django.core.exceptions import ValidationError

        if self.assessment_code.startswith("CA"):
            if self.max_score > 10:
                raise ValidationError(
                    f"CA assessments cannot exceed 10 points. You set {self.max_score}."
                )
        elif self.assessment_code == "TEST":
            if self.max_score > 10:
                raise ValidationError(
                    "Test assessments cannot exceed 10 points."
                )
        elif self.assessment_code == "EXAM":
            if self.max_score != 60:
                raise ValidationError(
                    f"Exam must be exactly 60 points. You set {self.max_score}."
                )

        # Check total CA for this subject/class/term doesn't exceed 40
        if self.assessment_code.startswith("CA"):
            ca_total = (
                Assessment.objects.filter(
                    assignment__classroom=self.assignment.classroom,
                    assignment__subject=self.assignment.subject,
                    assignment__term=self.assignment.term,
                    assessment_code__startswith="CA",
                )
                .exclude(pk=self.pk)
                .aggregate(total=models.Sum("max_score"))["total"]
                or 0
            )
            if ca_total + self.max_score > 40:
                raise ValidationError(
                    f"Total CA for this subject cannot exceed 40. "
                    f"Current total: {ca_total}, trying to add: {self.max_score} = {ca_total + self.max_score}"
                )

    def save(self, *args, **kwargs):
        """Call clean before saving"""
        self.clean()
        super().save(*args, **kwargs)

    def lock_scores(self, admin_user):
        """Lock all scores for this assessment"""
        from django.utils import timezone

        self.is_locked = True
        self.locked_by = admin_user
        self.locked_at = timezone.now()
        self.save(update_fields=["is_locked", "locked_by", "locked_at"])

    def unlock_scores(self):
        """Unlock all scores for this assessment"""
        self.is_locked = False
        self.locked_by = None
        self.locked_at = None
        self.save(update_fields=["is_locked", "locked_by", "locked_at"])

    def __str__(self):
        return f"{self.title} - {self.assignment.subject.name} ({self.assessment_code})"

    class Meta:
        ordering = ["-date"]
        verbose_name = "Assessment"
        verbose_name_plural = "Assessments"


# In academics/models.py - Replace your StudentScore model with this:


class StudentScore(models.Model):
    """Student's score for an assessment"""

    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="scores"
    )
    student = models.ForeignKey(
        "records.Student", on_delete=models.CASCADE, related_name="scores"
    )
    score = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0)]
    )
    # ADD THESE TWO FIELDS:
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade = models.CharField(max_length=2, default="F")

    remarks = models.TextField(blank=True)
    submitted_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_percentage(self):
        """Calculate percentage from score"""
        if self.assessment and self.assessment.max_score > 0:
            return (float(self.score) / float(self.assessment.max_score)) * 100
        return 0

    def calculate_grade(self):
        """Calculate grade based on percentage"""
        pct = self.percentage
        if pct >= 80:
            return "A"
        elif pct >= 70:
            return "B"
        elif pct >= 60:
            return "C"
        elif pct >= 50:
            return "D"
        elif pct >= 40:
            return "E"
        else:
            return "F"

    def is_locked(self):
        """Check if this score is locked (assessment is locked)"""
        return self.assessment.is_locked if self.assessment else False

    def can_edit(self, user):
        """Check if user can edit this score"""
        if self.is_locked():
            return user.is_superuser
        return True

    def save(self, *args, **kwargs):
        """Auto-calculate percentage and grade before saving"""
        self.percentage = self.calculate_percentage()
        self.grade = self.calculate_grade()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.assessment.title}: {self.score}"

    class Meta:
        unique_together = ["assessment", "student"]
        ordering = ["-submitted_at"]
        verbose_name = "Student Score"
        verbose_name_plural = "Student Scores"


class TermResult(models.Model):
    """Aggregated term result for a student in a subject"""

    student = models.ForeignKey(
        "records.Student", on_delete=models.CASCADE, related_name="term_results"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)

    # Scores
    ca_total = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    exam_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Grading
    grade = models.CharField(max_length=2)
    position = models.IntegerField(null=True, blank=True)

    # Stats
    class_average = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    highest_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    lowest_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    # Teacher remarks
    teacher_remarks = models.TextField(blank=True)

    def calculate_grade(self):
        """Calculate grade from total score"""
        if self.total_score >= 75:
            return "A"
        elif self.total_score >= 65:
            return "B"
        elif self.total_score >= 55:
            return "C"
        elif self.total_score >= 45:
            return "D"
        elif self.total_score >= 40:
            return "E"
        else:
            return "F"

    def save(self, *args, **kwargs):
        self.total_score = self.ca_total + self.exam_score
        self.grade = self.calculate_grade()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name} ({self.term})"

    class Meta:
        unique_together = ["student", "subject", "term"]
        ordering = ["-term__session__start_date", "student__surname"]


class ReportCard(models.Model):
    """Full term report card for a student with comprehensive tracking and workflow support"""

    # Status choices for publishing workflow
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Published", "Published"),
        ("Archived", "Archived"),
    ]

    PERFORMANCE_RATING_CHOICES = [
        (5, "Excellent (90-100%)"),
        (4, "Good (80-89%)"),
        (3, "Average (70-79%)"),
        (2, "Fair (60-69%)"),
        (1, "Poor (Below 60%)"),
        (0, "N/A"),
    ]

    student = models.ForeignKey(
        "records.Student", on_delete=models.CASCADE, related_name="report_cards"
    )
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)

    # Overall stats
    total_score = models.DecimalField(max_digits=6, decimal_places=2)
    average_score = models.DecimalField(max_digits=5, decimal_places=2)
    position = models.IntegerField()
    out_of = models.IntegerField()  # Total students in class

    # Attendance
    days_present = models.IntegerField(default=0)
    days_absent = models.IntegerField(default=0)
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Attendance percentage (0-100)",
    )

    # Remarks
    class_teacher_remarks = models.TextField(blank=True)
    principal_remarks = models.TextField(blank=True)

    # --- Affective & Psychomotor Domains (Skills Assessment) ---
    SKILL_RATING_CHOICES = [
        (5, "Excellent"),
        (4, "Good"),
        (3, "Average"),
        (2, "Fair"),
        (1, "Poor"),
        (0, "N/A"),
    ]
    # Affective (Character & Conduct)
    punctuality = models.IntegerField(choices=SKILL_RATING_CHOICES, default=0)
    attendance_in_class = models.IntegerField(choices=SKILL_RATING_CHOICES, default=0)
    honesty = models.IntegerField(choices=SKILL_RATING_CHOICES, default=0)
    neatness = models.IntegerField(choices=SKILL_RATING_CHOICES, default=0)
    discipline = models.IntegerField(choices=SKILL_RATING_CHOICES, default=0)
    participation = models.IntegerField(choices=SKILL_RATING_CHOICES, default=0)

    # Psychomotor (Practical Skills)
    handwriting = models.IntegerField(choices=SKILL_RATING_CHOICES, default=0)
    sports_and_games = models.IntegerField(choices=SKILL_RATING_CHOICES, default=0)
    creative_skills = models.IntegerField(choices=SKILL_RATING_CHOICES, default=0)

    # --- Performance Tracking & Analytics ---
    performance_trend = models.CharField(
        max_length=20,
        choices=[
            ("Improving", "Improving"),
            ("Stable", "Stable"),
            ("Declining", "Declining"),
            ("Inconsistent", "Inconsistent"),
        ],
        default="Stable",
        help_text="Trend compared to previous term",
    )
    color_coded_performance = models.CharField(
        max_length=50,
        choices=[
            ("Green", "Excellent (Top Performer)"),
            ("Blue", "Good (High Performer)"),
            ("Yellow", "Average (Meets Standard)"),
            ("Orange", "Fair (Below Standard)"),
            ("Red", "Poor (Intervention Needed)"),
        ],
        default="Yellow",
        help_text="Color indicator for quick performance assessment",
    )
    benchmark_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Store benchmark data: class_avg, national_avg, target_score",
    )

    # --- Publishing Workflow & Status Management ---
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Draft",
        help_text="Report card status for workflow management",
    )

    # Timestamps for workflow tracking
    generated_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    printed_at = models.DateTimeField(null=True, blank=True)
    exported_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    # Legacy field for backwards compatibility
    is_published = models.BooleanField(default=False)

    # --- Recommendations & Next Steps ---
    next_term_recommendation = models.CharField(
        max_length=100,
        choices=[
            ("Promoted", "Promoted to next class"),
            ("Promoted with Caution", "Promoted with caution"),
            ("Retained", "Retained in same class"),
            ("Special Intervention", "Special intervention needed"),
            ("Referred to Counselor", "Referred to counselor"),
        ],
        blank=True,
        help_text="Academic recommendation for next term",
    )
    internal_notes = models.TextField(
        blank=True, help_text="Internal notes for staff (not visible to students)"
    )

    def __str__(self):
        return f"{self.student.full_name} - {self.term} ({self.status})"

    def get_skill_fields(self):
        """Returns a dictionary of skill fields and their labels for template iteration."""
        return {
            "punctuality": "Punctuality",
            "attendance_in_class": "Attendance",
            "honesty": "Honesty",
            "neatness": "Neatness",
            "discipline": "Discipline",
            "participation": "Participation",
            "handwriting": "Handwriting",
            "sports_and_games": "Sports/Games",
            "creative_skills": "Creative Skills",
        }

    def get_performance_color(self):
        """Return CSS color class based on average score"""
        avg = float(self.average_score)
        if avg >= 90:
            return "green"
        elif avg >= 80:
            return "blue"
        elif avg >= 70:
            return "yellow"
        elif avg >= 60:
            return "orange"
        else:
            return "red"

    def get_performance_label(self):
        """Return performance label based on average score"""
        avg = float(self.average_score)
        if avg >= 90:
            return "Excellent"
        elif avg >= 80:
            return "Good"
        elif avg >= 70:
            return "Average"
        elif avg >= 60:
            return "Fair"
        else:
            return "Poor"

    def calculate_attendance_percentage(self):
        """Calculate attendance percentage"""
        total_days = self.days_present + self.days_absent
        if total_days > 0:
            percentage = (self.days_present / total_days) * 100
            self.attendance_percentage = percentage
            self.save(update_fields=["attendance_percentage"])
        return self.attendance_percentage

    def publish(self):
        """Publish report card to student"""
        from django.utils import timezone

        self.status = "Published"
        self.is_published = True
        self.published_at = timezone.now()
        self.save()

    def unpublish(self):
        """Unpublish report card"""
        self.status = "Draft"
        self.is_published = False
        self.published_at = None
        self.save()

    def archive(self):
        """Archive report card"""
        from django.utils import timezone

        self.status = "Archived"
        self.archived_at = timezone.now()
        self.save()

    class Meta:
        unique_together = ["student", "term"]
        ordering = ["-term__session__start_date", "student__surname"]
        verbose_name = "Report Card"
        verbose_name_plural = "Report Cards"
        indexes = [
            models.Index(fields=["status", "term"]),
            models.Index(fields=["student", "term"]),
            models.Index(fields=["-published_at"]),
        ]


class PerformanceComment(models.Model):
    """Pre-defined comments for quick teacher remarks"""

    text = models.TextField()
    category = models.CharField(max_length=50)  # Excellent, Good, Average, Poor
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category}: {self.text[:50]}"

    class Meta:
        ordering = ["category"]


class Attendance(models.Model):
    """Model to track student attendance."""

    ATTENDANCE_STATUS = [
        ("Present", "Present"),
        ("Absent", "Absent"),
        ("Late", "Late"),
        ("Excused", "Excused"),
    ]

    student = models.ForeignKey(
        "records.Student", on_delete=models.CASCADE, related_name="attendances"
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=ATTENDANCE_STATUS)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="academics_attendances",
    )

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"

    class Meta:
        unique_together = ["student", "date"]
        ordering = ["-date", "student__surname"]


class Timetable(models.Model):
    """Class timetable"""

    DAYS_OF_WEEK = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
    ]

    classroom = models.ForeignKey(
        "ClassRoom", on_delete=models.CASCADE, related_name="timetable"
    )
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    period_number = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    term = models.ForeignKey("Term", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.classroom} - {self.day_of_week} Period {self.period_number} - {self.subject.name}"

    class Meta:
        ordering = ["classroom", "day_of_week", "period_number"]
        unique_together = ["classroom", "day_of_week", "period_number", "term"]
