from django.db import models
from records.models import Student


class StudentOffense(models.Model):
    EVENT_CHOICES = [
        ("Discipline", "Discipline"),
        ("Bullying", "Bullying"),
        ("Incident", "Incident"),
        ("Accident", "Accident"),
    ]
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="committee_offenses",
        null=True,
        blank=True,
    )
    student_name = models.CharField(max_length=255)
    student_class = models.CharField(max_length=50)
    offense_description = models.TextField()
    offense_date = models.DateField()
    witness_name = models.CharField(max_length=255)
    victim_name = models.CharField(max_length=255)
    victim_class = models.CharField(max_length=50, blank=True, null=True)
    care_given_to_victim = models.TextField()
    location = models.CharField(max_length=255)
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    sanction = models.CharField(max_length=255)
    parent_notified = models.BooleanField(default=False)
    other_comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student_name} - {self.offense_description}"


class TeacherReport(models.Model):
    teacher_name = models.CharField(max_length=255)
    offense = models.ForeignKey(
        StudentOffense, on_delete=models.CASCADE, related_name="reports"
    )
    report_date = models.DateTimeField(auto_now_add=True)
    report_details = models.TextField()

    def __str__(self):
        return f"Report by {self.teacher_name} on {self.report_date}"
