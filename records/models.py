from django.db import models
from django.core.exceptions import ValidationError
from datetime import date
import os


class Student(models.Model):
    surname = models.CharField(max_length=100)
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
    admission_no = models.CharField(max_length=50, unique=True)
    nin_no = models.CharField(max_length=50, blank=True, null=True)
    class_on_entry = models.CharField(max_length=50)
    date_of_entry = models.DateField()
    class_at_present = models.CharField(max_length=50)
    student_image = models.ImageField(upload_to="students/images/", blank=True, null=True)

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['admission_no']),
            models.Index(fields=['surname', 'other_name']),
            models.Index(fields=['class_at_present']),
        ]

    @property
    def age(self):
        """Calculate age from date of birth"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def full_name(self):
        """Return full name"""
        return f"{self.surname} {self.other_name or ''}".strip()

    def __str__(self):
        return f"{self.full_name} ({self.admission_no})"


class StudentDocument(models.Model):
    DOCUMENT_TYPES = [
        ('birth_certificate', 'Birth Certificate'),
        ('nin', 'National Identification Number (NIN)'),
        ('immunization_card', 'Immunization Card'),
        ('waec_result', 'WAEC Result'),
        ('neco_result', 'NECO Result'),
        ('transfer_certificate', 'Transfer Certificate'),
        ('testimonial', 'Testimonial'),
        ('passport', 'Passport Photo'),
        ('medical_report', 'Medical Report'),
        ('other', 'Other Document'),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(
        max_length=50, 
        choices=DOCUMENT_TYPES,
        help_text="Type of document being uploaded",
        default='other'
    )
    name = models.CharField(
        max_length=100,
        help_text="Custom name/description for the document"
    )
    file = models.FileField(upload_to="students/documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True, help_text="Additional notes about the document")

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.name} for {self.student.full_name}"

    @property
    def file_extension(self):
        """Get file extension"""
        return os.path.splitext(self.file.name)[1].lower()

    @property
    def is_image(self):
        """Check if the file is an image"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return self.file_extension in image_extensions

    @property
    def is_pdf(self):
        """Check if the file is a PDF"""
        return self.file_extension == '.pdf'

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