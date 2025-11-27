# academics/forms.py

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
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
    Timetable,
    ReportCard,
    PerformanceComment,
)
from records.models import Student


# ============================================
# Academic Session & Term Forms
# ============================================


class AcademicSessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = ["name", "start_date", "end_date", "is_current"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., 2024/2025"}
            ),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "is_current": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date <= start_date:
            raise ValidationError("End date must be after start date.")

        return cleaned_data


class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ["session", "name", "start_date", "end_date", "is_current"]
        widgets = {
            "session": forms.Select(attrs={"class": "form-select"}),
            "name": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "is_current": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If session is selected, limit term choices to only those not already used
        session = self.initial.get("session") or self.data.get("session")
        if session:
            from .models import Term, AcademicSession

            try:
                session_obj = AcademicSession.objects.get(pk=session)
                used_terms = set(
                    Term.objects.filter(session=session_obj).values_list(
                        "name", flat=True
                    )
                )
                all_terms = [choice[0] for choice in Term.TERM_CHOICES]
                available_terms = [
                    (t, dict(Term.TERM_CHOICES)[t])
                    for t in all_terms
                    if t not in used_terms
                ]
                self.fields["name"].choices = available_terms
            except AcademicSession.DoesNotExist:
                pass

    def clean(self):
        cleaned_data = super().clean()
        session = cleaned_data.get("session")
        name = cleaned_data.get("name")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date <= start_date:
            raise ValidationError("End date must be after start date.")

        # Prevent more than 3 terms per session
        if session:
            from .models import Term

            term_count = Term.objects.filter(session=session).count()
            if self.instance.pk is None and term_count >= 3:
                raise ValidationError(
                    "You cannot create more than 3 terms for a session."
                )
            # Prevent duplicate term name for session
            if (
                name
                and Term.objects.filter(session=session, name=name)
                .exclude(pk=getattr(self.instance, "pk", None))
                .exists()
            ):
                raise ValidationError(f"{name} term already exists for this session.")

        return cleaned_data


# ============================================
# Subject & Class Management Forms
# ============================================


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code", "description", "is_core"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., Mathematics"}
            ),
            "code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., MATH101"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Subject description (optional)",
                }
            ),
            "is_core": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ClassRoomForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = ["level", "arm", "session", "class_teacher"]
        widgets = {
            "level": forms.Select(attrs={"class": "form-select"}),
            "arm": forms.Select(attrs={"class": "form-select"}),
            "session": forms.Select(attrs={"class": "form-select"}),
            "class_teacher": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to show only staff users
        self.fields["class_teacher"].queryset = User.objects.filter(is_staff=True)


class SubjectAssignmentForm(forms.ModelForm):
    class Meta:
        model = SubjectAssignment
        fields = ["classroom", "subject", "teacher", "term"]
        widgets = {
            "classroom": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "teacher": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to show only staff users
        self.fields["teacher"].queryset = User.objects.filter(is_staff=True)


# ============================================
# Assessment Forms
# ============================================


class AssessmentTypeForm(forms.ModelForm):
    class Meta:
        model = AssessmentType
        fields = ["name", "code", "weight", "max_score", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., First CA"}
            ),
            "code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., CA1"}
            ),
            "weight": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0-100",
                    "min": 0,
                    "max": 100,
                }
            ),
            "max_score": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "e.g., 100", "min": 1}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional description",
                }
            ),
        }

    def clean_weight(self):
        weight = self.cleaned_data.get("weight")
        if weight < 0 or weight > 100:
            raise ValidationError("Weight must be between 0 and 100.")
        return weight


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = [
            "assignment",
            "assessment_type",
            "assessment_code",
            "title",
            "date",
            "max_score",
            "instructions",
        ]
        widgets = {
            "assignment": forms.Select(attrs={"class": "form-select"}),
            "assessment_type": forms.Select(attrs={"class": "form-select"}),
            "assessment_code": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_assessment_code",
                    "data-toggle": "tooltip",
                    "title": "Select assessment type: CA1/CA2/CA3 (max 10), TEST (max 10), EXAM (60)",
                }
            ),
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., Week 1 Test"}
            ),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "max_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "100",
                    "min": 1,
                    "id": "id_max_score",
                }
            ),
            "instructions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Instructions for students (optional)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user and not self.user.is_superuser:
            # For non-superusers, show assignments from active sessions, prioritizing the current term.
            self.fields["assignment"].queryset = (
                SubjectAssignment.objects.filter(
                    teacher=self.user, term__session__is_current=True
                )
                .select_related("classroom", "subject", "term")
                .order_by("-term__is_current", "-term__start_date")
            )

        # Add help text to max_score field
        self.fields["max_score"].help_text = (
            "CA: max 10 points | TEST: max 10 points | EXAM: 60 points | "
            "Total CA cannot exceed 40"
        )

    def clean(self):
        """Validate assessment score constraints"""
        cleaned_data = super().clean()
        assessment_code = cleaned_data.get("assessment_code")
        max_score = cleaned_data.get("max_score")
        assignment = cleaned_data.get("assignment")

        if not assessment_code or not max_score:
            return cleaned_data

        # Validate based on assessment code
        if assessment_code.startswith("CA"):
            if max_score > 10:
                raise ValidationError(
                    f"❌ CA assessments cannot exceed 10 points. You set {max_score}. "
                    "Please reduce the score to 10 or less."
                )

            # Check total CA for this subject/class/term
            if assignment:
                ca_total = (
                    Assessment.objects.filter(
                        assignment__classroom=assignment.classroom,
                        assignment__subject=assignment.subject,
                        assignment__term=assignment.term,
                        assessment_code__startswith="CA",
                    )
                    .exclude(pk=self.instance.pk if self.instance else None)
                    .aggregate(total=models.Sum("max_score"))["total"]
                    or 0
                )

                if ca_total + max_score > 40:
                    raise ValidationError(
                        f"❌ Total CA cannot exceed 40 points. "
                        f"Current CA total: {ca_total}, trying to add: {max_score} = {ca_total + max_score}. "
                        f"Please reduce the score. (Max allowed: {40 - ca_total})"
                    )

        elif assessment_code == "TEST":
            if max_score > 10:
                raise ValidationError(
                    f"❌ Test assessments cannot exceed 10 points. You set {max_score}. "
                    "Please reduce the score to 10 or less."
                )

        elif assessment_code == "EXAM":
            if max_score != 60:
                raise ValidationError(
                    f"❌ Exam must be exactly 60 points. You set {max_score}. "
                    "Please set the score to 60."
                )

        return cleaned_data


# ============================================
# Score Entry Forms
# ============================================


class StudentScoreForm(forms.ModelForm):
    class Meta:
        model = StudentScore
        fields = ["student", "score", "remarks"]
        widgets = {
            "student": forms.Select(attrs={"class": "form-select"}),
            "score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0",
                    "step": "0.01",
                    "min": 0,
                }
            ),
            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Optional remarks",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.assessment = kwargs.pop("assessment", None)
        super().__init__(*args, **kwargs)

        if self.assessment:
            # Set max score from assessment
            self.fields["score"].widget.attrs["max"] = self.assessment.max_score

            # Show lock warning if assessment is locked
            if self.assessment.is_locked:
                locked_by_name = (
                    self.assessment.locked_by.get_full_name()
                    or self.assessment.locked_by.username
                    if self.assessment.locked_by
                    else "Admin"
                )
                self.fields["score"].widget.attrs["readonly"] = True
                self.fields["remarks"].widget.attrs["readonly"] = True
                self.fields[
                    "score"
                ].help_text = f"🔒 LOCKED by {locked_by_name} on {self.assessment.locked_at.strftime('%Y-%m-%d %H:%M')}"

    def clean(self):
        """Check if assessment is locked and prevent editing if so"""
        cleaned_data = super().clean()

        # Check if assessment is locked
        if self.assessment and self.assessment.is_locked:
            raise ValidationError(
                "🔒 This assessment is LOCKED. Only admins can modify scores. "
                f"Locked by: {self.assessment.locked_by.username if self.assessment.locked_by else 'Admin'} "
                f"at {self.assessment.locked_at.strftime('%Y-%m-%d %H:%M') if self.assessment.locked_at else 'N/A'}"
            )

        return cleaned_data

    def clean_score(self):
        score = self.cleaned_data.get("score")
        if self.assessment and score > self.assessment.max_score:
            raise ValidationError(f"Score cannot exceed {self.assessment.max_score}")
        return score


class BulkScoreEntryForm(forms.Form):
    """Form for entering scores for multiple students at once"""

    def __init__(self, *args, **kwargs):
        self.assessment = kwargs.pop("assessment", None)
        self.students = kwargs.pop("students", [])
        super().__init__(*args, **kwargs)

        # Dynamically create fields for each student
        for student in self.students:
            field_name = f"score_{student.id}"
            self.fields[field_name] = forms.DecimalField(
                label=student.full_name,
                required=False,
                max_digits=5,
                decimal_places=2,
                min_value=0,
                max_value=self.assessment.max_score if self.assessment else 100,
                widget=forms.NumberInput(
                    attrs={"class": "form-control", "placeholder": "0", "step": "0.01"}
                ),
            )

            # Add remarks field
            remarks_field = f"remarks_{student.id}"
            self.fields[remarks_field] = forms.CharField(
                required=False,
                widget=forms.TextInput(
                    attrs={
                        "class": "form-control form-control-sm",
                        "placeholder": "Remarks (optional)",
                    }
                ),
            )

    def clean(self):
        cleaned_data = super().clean()

        # Manually process each student's score and remarkas from the submitted data
        for student in self.students:
            score_field_name = f"score_{student.id}"
            remarks_field_name = f"remarks_{student.id}"

            score_val = self.data.get(score_field_name)

            if score_val is not None and score_val != "":
                try:
                    score = forms.DecimalField(
                        max_value=self.assessment.max_score, min_value=0
                    ).clean(score_val)
                    cleaned_data[score_field_name] = score
                except ValidationError as e:
                    self.add_error(score_field_name, e)

            # Remarks are optional and don't need strict validation here
            remarks_val = self.data.get(remarks_field_name, "")
            cleaned_data[remarks_field_name] = remarks_val

        return cleaned_data


# ============================================
# Term Result Forms
# ============================================


class TermResultForm(forms.ModelForm):
    class Meta:
        model = TermResult
        fields = [
            "student",
            "subject",
            "term",
            "classroom",
            "ca_total",
            "exam_score",
            "teacher_remarks",
        ]
        widgets = {
            "student": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "classroom": forms.Select(attrs={"class": "form-select"}),
            "ca_total": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "0", "step": "0.01"}
            ),
            "exam_score": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "0", "step": "0.01"}
            ),
            "teacher_remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Teacher remarks",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        ca_total = cleaned_data.get("ca_total", 0)
        exam_score = cleaned_data.get("exam_score", 0)

        if ca_total > 40:
            raise ValidationError("CA total cannot exceed 40")

        if exam_score > 60:
            raise ValidationError("Exam score cannot exceed 60")

        return cleaned_data


class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = [
            "classroom",
            "day_of_week",
            "period_number",
            "start_time",
            "end_time",
            "subject",
            "teacher",
            "term",
            "is_active",
        ]
        widgets = {
            "classroom": forms.Select(attrs={"class": "form-select"}),
            "day_of_week": forms.Select(attrs={"class": "form-select"}),
            "period_number": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),
            "start_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "end_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "teacher": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["teacher"].queryset = User.objects.filter(is_staff=True)
        self.fields["subject"].queryset = Subject.objects.all().order_by("name")
        self.fields["classroom"].queryset = ClassRoom.objects.filter(
            session__is_current=True
        ).order_by("level", "arm")
        self.fields["term"].queryset = Term.objects.filter(is_current=True).order_by(
            "-session__start_date", "name"
        )

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned_data


# ============================================
# Report Card Forms
# ============================================


class ReportCardForm(forms.ModelForm):
    class Meta:
        model = ReportCard
        fields = [
            "student",
            "term",
            "classroom",
            "days_present",
            "days_absent",
            "class_teacher_remarks",
            "principal_remarks",
            "is_published",
        ]
        widgets = {
            "student": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "classroom": forms.Select(attrs={"class": "form-select"}),
            "days_present": forms.NumberInput(
                attrs={"class": "form-control", "min": 0}
            ),
            "days_absent": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "class_teacher_remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Class teacher remarks",
                }
            ),
            "principal_remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Principal remarks",
                }
            ),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class BulkReportCardGenerationForm(forms.Form):
    """Form for generating report cards for multiple students"""

    term = forms.ModelChoiceField(
        queryset=Term.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select Term",
    )
    classroom = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select Class",
    )


# ============================================
# Filter & Search Forms
# ============================================


class PerformanceFilterForm(forms.Form):
    session = forms.ModelChoiceField(
        queryset=AcademicSession.objects.all(),
        required=False,
        empty_label="All Sessions",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    term = forms.ModelChoiceField(
        queryset=Term.objects.all(),
        required=False,
        empty_label="All Terms",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    classroom = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        required=False,
        empty_label="All Classes",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        empty_label="All Subjects",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.all().order_by("surname", "other_name"),
        required=False,
        empty_label="All Students",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    min_score = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0"}),
    )
    max_score = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "100"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preselect current session/term if form is not bound
        if not self.is_bound:
            try:
                current_term = Term.objects.filter(is_current=True).first()
                if current_term:
                    self.initial.setdefault("term", current_term.id)
                    self.initial.setdefault("session", current_term.session_id)
            except Exception:
                pass


class ScoreImportForm(forms.Form):
    """Form for importing scores from Excel/CSV"""

    assessment = forms.ModelChoiceField(
        queryset=Assessment.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select Assessment",
    )
    file = forms.FileField(
        widget=forms.FileInput(
            attrs={"class": "form-control", "accept": ".xlsx,.xls,.csv"}
        ),
        label="Upload File",
        help_text="Accepted formats: Excel (.xlsx, .xls) or CSV (.csv)",
    )

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            # Check file extension
            ext = file.name.split(".")[-1].lower()
            if ext not in ["xlsx", "xls", "csv"]:
                raise ValidationError(
                    "Invalid file format. Please upload Excel or CSV file."
                )

            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("File size must be under 5MB.")

        return file


# ============================================
# Performance Comment Form
# ============================================


class PerformanceCommentForm(forms.ModelForm):
    class Meta:
        model = PerformanceComment
        fields = ["text", "category", "is_active"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter comment text",
                }
            ),
            "category": forms.Select(
                attrs={"class": "form-select"},
                choices=[
                    ("Excellent", "Excellent"),
                    ("Very Good", "Very Good"),
                    ("Good", "Good"),
                    ("Average", "Average"),
                    ("Below Average", "Below Average"),
                    ("Poor", "Poor"),
                ],
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# ============================================
# Enhanced Report Card Workflow Forms
# ============================================


class EnhancedReportCardForm(forms.ModelForm):
    """Enhanced form for creating/editing report cards with all new fields"""

    class Meta:
        model = ReportCard
        fields = [
            "student",
            "term",
            "classroom",
            "days_present",
            "days_absent",
            "attendance_percentage",
            "class_teacher_remarks",
            "principal_remarks",
            "performance_trend",
            "next_term_recommendation",
            "status",
            "punctuality",
            "attendance_in_class",
            "honesty",
            "neatness",
            "discipline",
            "participation",
            "handwriting",
            "sports_and_games",
            "creative_skills",
            "internal_notes",
        ]
        widgets = {
            "student": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "classroom": forms.Select(attrs={"class": "form-select"}),
            "days_present": forms.NumberInput(
                attrs={"class": "form-control", "min": 0}
            ),
            "days_absent": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "attendance_percentage": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "max": 100, "step": 0.01}
            ),
            "class_teacher_remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Class teacher's remarks on overall performance",
                }
            ),
            "principal_remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Principal's remarks and overall assessment",
                }
            ),
            "performance_trend": forms.Select(attrs={"class": "form-select"}),
            "next_term_recommendation": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "punctuality": forms.Select(attrs={"class": "form-select"}),
            "attendance_in_class": forms.Select(attrs={"class": "form-select"}),
            "honesty": forms.Select(attrs={"class": "form-select"}),
            "neatness": forms.Select(attrs={"class": "form-select"}),
            "discipline": forms.Select(attrs={"class": "form-select"}),
            "participation": forms.Select(attrs={"class": "form-select"}),
            "handwriting": forms.Select(attrs={"class": "form-select"}),
            "sports_and_games": forms.Select(attrs={"class": "form-select"}),
            "creative_skills": forms.Select(attrs={"class": "form-select"}),
            "internal_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Internal notes for staff only",
                }
            ),
        }


class ReportCardPublishForm(forms.Form):
    """Form for publishing report cards in bulk"""

    term = forms.ModelChoiceField(
        queryset=Term.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select Term",
    )
    classroom = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select Class",
    )
    publish_all = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Publish all report cards for this class/term",
    )


class ReportCardStatusForm(forms.Form):
    """Form for changing report card status"""

    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Published", "Published"),
        ("Archived", "Archived"),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="New Status",
    )
    notify_student = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Notify student when published",
    )


class ReportCardBenchmarkForm(forms.Form):
    """Form for setting benchmark data"""

    class_average = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Class average score",
                "step": 0.01,
            }
        ),
    )
    national_average = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "National average (optional)",
                "step": 0.01,
            }
        ),
    )
    target_score = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Target score for this class",
                "step": 0.01,
            }
        ),
    )
