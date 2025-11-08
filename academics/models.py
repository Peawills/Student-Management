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
    """Individual assessment/test"""

    assignment = models.ForeignKey(SubjectAssignment, on_delete=models.CASCADE)
    assessment_type = models.ForeignKey(AssessmentType, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    date = models.DateField()
    max_score = models.IntegerField(default=100)
    instructions = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.assignment.subject.name}"

    class Meta:
        ordering = ["-date"]


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
    """Full term report card for a student"""

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

    # Remarks
    class_teacher_remarks = models.TextField(blank=True)
    principal_remarks = models.TextField(blank=True)

    # Dates
    generated_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.full_name} - {self.term} Report"

    class Meta:
        unique_together = ["student", "term"]
        ordering = ["-term__session__start_date"]


class PerformanceComment(models.Model):
    """Pre-defined comments for quick teacher remarks"""

    text = models.TextField()
    category = models.CharField(max_length=50)  # Excellent, Good, Average, Poor
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category}: {self.text[:50]}"

    class Meta:
        ordering = ["category"]
