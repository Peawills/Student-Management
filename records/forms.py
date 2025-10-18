from django import forms
from django.core.exceptions import ValidationError
from .models import Student, StudentDocument
from datetime import date


class StudentForm(forms.ModelForm):
    """Enhanced form for creating and updating students"""

    class Meta:
        model = Student
        fields = [
            "surname",
            "other_name",
            "residential_address",
            "permanent_home_address",
            "nationality",
            "state_of_origin",
            "lga",
            "date_of_birth",
            "place_of_birth",
            "religion",
            "denomination",
            "sex",
            "nin_no",
            "class_on_entry",
            "date_of_entry",
            "class_at_present",
            "student_image",
            "father_name",
            "father_address",
            "father_occupation",
            "father_educational_level",
            "father_mobile",
            "mother_name",
            "mother_address",
            "mother_occupation",
            "mother_educational_level",
            "mother_mobile",
            "guardian_name",
            "guardian_address",
            "guardian_occupation",
            "guardian_mobile",
            "prev_schools",
            "visually_impaired",
            "deaf",
            "physically_disabled",
            "mentally_impaired",
            "others",
        ]

        widgets = {
            "surname": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter surname"}
            ),
            "other_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter other names"}
            ),
            "residential_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter residential address",
                }
            ),
            "permanent_home_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter permanent home address",
                }
            ),
            "nationality": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., Nigerian"}
            ),
            "state_of_origin": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter state of origin"}
            ),
            "lga": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter LGA"}
            ),
            "date_of_birth": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "place_of_birth": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter place of birth"}
            ),
            "religion": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Christianity, Islam",
                }
            ),
            "denomination": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Catholic, Anglican",
                }
            ),
            "sex": forms.Select(attrs={"class": "form-select"}),
            "admission_no": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter unique admission number",
                }
            ),
            "nin_no": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter NIN number"}
            ),
            "class_on_entry": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., JSS 1"}
            ),
            "date_of_entry": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "class_at_present": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., SS 2"}
            ),
            "student_image": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "father_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter father's full name",
                }
            ),
            "father_address": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "father_occupation": forms.TextInput(attrs={"class": "form-control"}),
            "father_educational_level": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "father_mobile": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., +234..."}
            ),
            "mother_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter mother's full name",
                }
            ),
            "mother_address": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "mother_occupation": forms.TextInput(attrs={"class": "form-control"}),
            "mother_educational_level": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "mother_mobile": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., +234..."}
            ),
            "guardian_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter guardian's full name",
                }
            ),
            "guardian_address": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "guardian_occupation": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_mobile": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., +234..."}
            ),
            "prev_schools": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "List previous schools attended",
                }
            ),
            "visually_impaired": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "deaf": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "physically_disabled": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "mentally_impaired": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "others": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Any other health information",
                }
            ),
        }

    # admission_no is generated by the model and not editable via the form

    def clean_date_of_birth(self):
        """Validate date of birth"""
        dob = self.cleaned_data.get("date_of_birth")

        if dob:
            today = date.today()
            age = (
                today.year
                - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )

            if dob > today:
                raise ValidationError("Date of birth cannot be in the future.")

            if age < 3:
                raise ValidationError("Student must be at least 3 years old.")

            if age > 25:
                raise ValidationError(
                    "Please verify the date of birth. Age seems unusually high."
                )

        return dob

    def clean_date_of_entry(self):
        """Validate date of entry"""
        entry_date = self.cleaned_data.get("date_of_entry")
        dob = self.cleaned_data.get("date_of_birth")

        if entry_date:
            if entry_date > date.today():
                raise ValidationError("Entry date cannot be in the future.")

            if dob and entry_date < dob:
                raise ValidationError("Entry date cannot be before date of birth.")

        return entry_date

    def clean_student_image(self):
        """Validate student image"""
        image = self.cleaned_data.get("student_image")

        if image:
            # Check file size (max 2MB)
            if image.size > 2 * 1024 * 1024:
                raise ValidationError("Image file size cannot exceed 2MB.")

            # Check file extension
            allowed_extensions = ["jpg", "jpeg", "png", "gif"]
            ext = image.name.split(".")[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(
                    f"Only {', '.join(allowed_extensions)} files are allowed."
                )

        return image


class StudentDocumentForm(forms.ModelForm):
    """Form for uploading a single student document"""

    class Meta:
        model = StudentDocument
        fields = ["document_type", "name", "file", "notes"]

        widgets = {
            "document_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter document name/description",
                }
            ),
            "file": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*,.pdf,.doc,.docx",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Additional notes about this document (optional)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make document fields optional for create flow
        self.fields["document_type"].required = False
        self.fields["name"].required = False
        self.fields["file"].required = False

    def clean_file(self):
        """Validate document file"""
        file = self.cleaned_data.get("file")

        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 5MB.")

            # Check file extension
            allowed_extensions = ["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx"]
            ext = file.name.split(".")[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(
                    f"Only {', '.join(allowed_extensions)} files are allowed."
                )

        return file


class MultipleStudentDocumentForm(forms.Form):
    """Form for uploading multiple documents at once"""

    document_type = forms.ChoiceField(
        required=False,
        choices=StudentDocument.DOCUMENT_TYPES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Document Type",
    )

    name = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": 'Base name for documents (e.g., "Birth Certificate")',
            }
        ),
        label="Document Name",
    )

    class MultiFileInput(forms.ClearableFileInput):
        allow_multiple_selected = True

    files = forms.FileField(
        required=False,
        widget=MultiFileInput(
            attrs={
                "class": "form-control",
                "multiple": True,
                "accept": "image/*,.pdf,.doc,.docx",
            }
        ),
        label="Select Files",
        help_text="You can select multiple files. Max 5MB per file.",
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional notes (will apply to all uploaded documents)",
            }
        ),
        label="Notes",
    )

    def clean_files(self):
        """Validate multiple files"""
        files = self.files.getlist("files")

        if not files:
            return []

        if len(files) > 10:
            raise ValidationError("You can upload a maximum of 10 files at once.")

        for file in files:
            # Check file size
            if file.size > 5 * 1024 * 1024:
                raise ValidationError(f"File {file.name} exceeds 5MB.")

            # Check extension
            allowed_extensions = ["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx"]
            ext = file.name.split(".")[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(
                    f"File {file.name} has an invalid extension. "
                    f"Allowed: {', '.join(allowed_extensions)}"
                )

        return files


class StudentSearchForm(forms.Form):
    """Form for searching students"""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search by name or admission number...",
                "autocomplete": "off",
            }
        ),
        label="",
    )

    sex = forms.ChoiceField(
        required=False,
        choices=[("", "All Genders"), ("Male", "Male"), ("Female", "Female")],
        widget=forms.Select(attrs={"class": "form-select"}),
        label="",
    )

    klass = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Filter by class..."}
        ),
        label="",
    )

    sort = forms.ChoiceField(
        required=False,
        choices=[
            ("-id", "Newest First"),
            ("id", "Oldest First"),
            ("surname", "Name (A-Z)"),
            ("-surname", "Name (Z-A)"),
            ("admission_no", "Admission No. (Ascending)"),
            ("-admission_no", "Admission No. (Descending)"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
        label="",
    )
