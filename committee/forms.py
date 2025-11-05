from django import forms
from .models import StudentOffense, TeacherReport


class StudentOffenseForm(forms.ModelForm):
    class Meta:
        model = StudentOffense
        fields = [
            "student_name",
            "student_class",
            "offense_description",
            "offense_date",
            "witness_name",
            "victim_name",
            "victim_class",
            "care_given_to_victim",
            "location",
            "event_type",
            "sanction",
            "parent_notified",
            "other_comments",
        ]
        widgets = {
            "offense_description": forms.Textarea(attrs={"rows": 4}),
            "care_given_to_victim": forms.Textarea(attrs={"rows": 3}),
            "other_comments": forms.Textarea(attrs={"rows": 3}),
            "offense_date": forms.DateInput(attrs={"type": "date"}),
        }


class TeacherReportForm(forms.ModelForm):
    class Meta:
        model = TeacherReport
        fields = ["teacher_name", "report_details"]
        widgets = {
            "report_details": forms.Textarea(attrs={"rows": 4}),
        }
