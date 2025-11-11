from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date
import os


class Student(models.Model):
    surname = models.CharField(max_length=100)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_record",
    )
    other_name = models.CharField(max_length=100, blank=True, null=True)
    residential_address = models.TextField()
    permanent_home_address = models.TextField(blank=True, null=True)
    nationality = models.CharField(max_length=50)
    state_of_origin = models.CharField(max_length=50)
    lga = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=100)
    religion = models.CharField(max_length=50, blank=True, null=True)
    denomination = models.CharField(max_length=50, blank=True, null=True)
    sex = models.CharField(
        max_length=10, choices=[("Male", "Male"), ("Female", "Female")]
    )
    admission_no = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        editable=False,
        help_text="Automatically generated admission number",
    )
    nin_no = models.CharField(max_length=50, blank=True, null=True)
    class_on_entry = models.CharField(max_length=50)
    date_of_entry = models.DateField()
    class_at_present = models.CharField(max_length=50)
    classroom = models.ForeignKey(
        "academics.ClassRoom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        help_text="Select the student's current class",
    )
    student_image = models.ImageField(
        upload_to="students/images/", blank=True, null=True
    )
    is_active = models.BooleanField(
        default=True, help_text="Active students are shown in lists. Unselect this to archive a student."
    )
    graduation_session = models.ForeignKey(
        "academics.AcademicSession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The academic session the student graduated/was archived in.",
    )

    # Parent/Guardian info
    father_name = models.CharField(max_length=100)
    father_address = models.TextField(blank=True, null=True)
    father_occupation = models.CharField(max_length=100, blank=True, null=True)
    father_educational_level = models.CharField(max_length=100, blank=True, null=True)
    father_mobile = models.CharField(max_length=20, blank=True, null=True)

    mother_name = models.CharField(max_length=100)
    mother_address = models.TextField(blank=True, null=True)
    mother_occupation = models.CharField(max_length=100, blank=True, null=True)
    mother_educational_level = models.CharField(max_length=100, blank=True, null=True)
    mother_mobile = models.CharField(max_length=20, blank=True, null=True)

    guardian_name = models.CharField(max_length=100, blank=True, null=True)
    guardian_address = models.TextField(blank=True, null=True)
    guardian_occupation = models.CharField(max_length=100, blank=True, null=True)
    guardian_mobile = models.CharField(max_length=20, blank=True, null=True)

    # Previous Schools
    prev_schools = models.TextField(blank=True, null=True)

    # Special Health Status
    visually_impaired = models.BooleanField(default=False)
    deaf = models.BooleanField(default=False)
    physically_disabled = models.BooleanField(default=False)
    mentally_impaired = models.BooleanField(default=False)
    others = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["admission_no"]),
            models.Index(fields=["surname", "other_name"]),
            models.Index(fields=["class_at_present"]),
        ]

    @property
    def age(self):
        """Calculate age from date of birth"""
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

    @property
    def full_name(self):
        """Return full name"""
        return f"{self.surname} {self.other_name or ''}".strip()

    def __str__(self):
        return f"{self.full_name} ({self.admission_no})"

    def _generate_admission_no(self):
        """Generate a new admission number with YEAR-XXXX format (e.g., 2025-0001)."""
        year = timezone.now().year
        prefix = f"{year}-"
        # Find the last admission_no for this year; admission_no is zero-padded so lexicographic order works
        last = (
            Student.objects.filter(admission_no__startswith=prefix)
            .order_by("-admission_no")
            .first()
        )
        if last and last.admission_no:
            try:
                last_num = int(last.admission_no.split("-")[-1])
            except Exception:
                last_num = 0
        else:
            last_num = 0
        next_num = last_num + 1
        return f"{year}-{next_num:04d}"

    def save(self, *args, **kwargs):
        """Ensure updated_at auto-updates on every save and auto-generate admission_no on create.

        Admission numbers use YEAR-XXXX (e.g., 2025-0001). We attempt to generate a unique value and
        retry a few times if a race causes an IntegrityError.
        """
        is_create = self._state.adding
        
        # Sync class_at_present with the classroom foreign key
        if self.classroom:
            self.class_at_present = str(self.classroom)

        self.updated_at = timezone.now()

        if is_create and not self.admission_no:
            # Try a few times in case of a race condition where another process created the same number
            from django.db import IntegrityError

            for attempt in range(5):
                self.admission_no = self._generate_admission_no()
                try:
                    super().save(*args, **kwargs)
                    break
                except IntegrityError:
                    # Someone else created this admission_no concurrently; try again
                    if attempt == 4:
                        raise
                    continue
        else:
            super().save(*args, **kwargs)


class StudentDocument(models.Model):
    DOCUMENT_TYPES = [
        ("birth_certificate", "Birth Certificate"),
        ("nin", "National Identification Number (NIN)"),
        ("immunization_card", "Immunization Card"),
        ("waec_result", "WAEC Result"),
        ("neco_result", "NECO Result"),
        ("transfer_certificate", "Transfer Certificate"),
        ("testimonial", "Testimonial"),
        ("passport", "Passport Photo"),
        ("medical_report", "Medical Report"),
        ("other", "Other Document"),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPES,
        help_text="Type of document being uploaded",
        default="other",
    )
    name = models.CharField(
        max_length=100, help_text="Custom name/description for the document"
    )
    file = models.FileField(upload_to="students/documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(
        blank=True, null=True, help_text="Additional notes about the document"
    )

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.name} for {self.student.full_name}"

    @property
    def file_extension(self):
        """Get file extension"""
        return os.path.splitext(self.file.name)[1].lower()

    @property
    def is_image(self):
        """Check if the file is an image"""
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
        return self.file_extension in image_extensions

    @property
    def is_pdf(self):
        """Check if the file is a PDF"""
        return self.file_extension == ".pdf"

    @property
    def file_size_mb(self):
        """Get file size in MB"""
        if self.file:
            return round(self.file.size / (1024 * 1024), 2)
        return 0

    def clean(self):
        """Validate file size (max 5MB)"""
        if self.file:
            if self.file.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError("File size cannot exceed 5MB")


class StudentOffense(models.Model):
    OFFENSE_TYPES = [
        ("minor", "Minor"),
        ("major", "Major"),
        ("critical", "Critical"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="record_offenses",
        blank=True,
        null=True,
    )
    offense_type = models.CharField(
        max_length=20, choices=OFFENSE_TYPES, default="minor"
    )
    description = models.TextField()
    date_committed = models.DateField()
    action_taken = models.TextField()
    witness = models.CharField(max_length=200, blank=True, null=True)
    documented_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_committed"]
        verbose_name = "Student Offense"
        verbose_name_plural = "Student Offenses"

    def __str__(self):
        if self.student:
            return f"{self.student.full_name} - {self.get_offense_type_display()} Offense on {self.date_committed}"
        return f"Unassigned - {self.get_offense_type_display()} Offense on {self.date_committed}"
