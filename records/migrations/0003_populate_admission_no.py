from django.db import migrations


def populate_admission_no(apps, schema_editor):
    Student = apps.get_model("records", "Student")
    from django.utils import timezone

    today = timezone.now()
    year = today.year
    prefix = f"{year}-"

    # Start counter at existing max for the year
    last = (
        Student.objects.filter(admission_no__startswith=prefix)
        .order_by("-admission_no")
        .first()
    )
    if last and last.admission_no:
        try:
            counter = int(last.admission_no.split("-")[-1])
        except Exception:
            counter = 0
    else:
        counter = 0

    qs = Student.objects.filter(admission_no__isnull=True) | Student.objects.filter(
        admission_no=""
    )
    for student in qs.order_by("pk"):
        counter += 1
        student.admission_no = f"{year}-{counter:04d}"
        student.save()


class Migration(migrations.Migration):
    dependencies = [
        ("records", "0002_alter_student_created_at_alter_student_updated_at"),
    ]

    operations = [
        migrations.RunPython(
            populate_admission_no, reverse_code=migrations.RunPython.noop
        ),
    ]
