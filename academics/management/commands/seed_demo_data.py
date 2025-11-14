from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from academics.models import (
    AcademicSession,
    Term,
    Subject,
    ClassRoom,
    SubjectAssignment,
    AssessmentType,
    Assessment,
    StudentScore,
    TermResult,
)
from records.models import Student


class Command(BaseCommand):
    help = "Seed minimal demo data for Performance Analytics (classes, subjects, students, assessments, scores)"

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=15, help="Number of students to create")

    @transaction.atomic
    def handle(self, *args, **options):
        num_students = options["students"]
        now = timezone.now()

        # Ensure session/term
        session = AcademicSession.objects.filter(is_current=True).first()
        if not session:
            session = AcademicSession.objects.create(
                name=f"{now.year}/{now.year + 1}",
                start_date=now.date(),
                end_date=now.date(),
                is_current=True,
            )
        term = Term.objects.filter(is_current=True, session=session).first()
        if not term:
            term = Term.objects.create(
                session=session,
                name="First",
                start_date=now.date(),
                end_date=now.date(),
                is_current=True,
            )

        # Ensure a staff user (teacher)
        teacher, _ = User.objects.get_or_create(
            username="teacher1",
            defaults={"first_name": "Terry", "last_name": "Teacher", "is_staff": True},
        )
        teacher.is_staff = True
        teacher.set_password("password123")
        teacher.save()

        # Create a class
        classroom, _ = ClassRoom.objects.get_or_create(
            level="JSS1", arm="A", session=session, defaults={"class_teacher": teacher}
        )

        # Subjects
        math, _ = Subject.objects.get_or_create(name="Mathematics", defaults={"code": "MATH"})
        eng, _ = Subject.objects.get_or_create(name="English", defaults={"code": "ENG"})

        # Assessment types
        ca_type, _ = AssessmentType.objects.get_or_create(
            code="CA1", defaults={"name": "First CA", "weight": 40, "max_score": 40}
        )
        exam_type, _ = AssessmentType.objects.get_or_create(
            code="EXAM", defaults={"name": "Examination", "weight": 60, "max_score": 60}
        )

        # Assign subjects to class for current term
        assg_math, _ = SubjectAssignment.objects.get_or_create(
            classroom=classroom, subject=math, teacher=teacher, term=term
        )
        assg_eng, _ = SubjectAssignment.objects.get_or_create(
            classroom=classroom, subject=eng, teacher=teacher, term=term
        )

        # Students
        created_students = []
        existing_count = Student.objects.filter(classroom=classroom).count()
        to_create = max(0, num_students - existing_count)
        for i in range(1, to_create + 1):
            s = Student.objects.create(
                surname=f"Student{i}",
                other_name="Demo",
                sex="Male" if i % 2 == 0 else "Female",
                residential_address="123 Demo Street",
                permanent_home_address="123 Demo Street",
                nationality="Nigeria",
                state_of_origin="Lagos",
                lga="Ikeja",
                date_of_birth=timezone.now().date().replace(year=now.year - (10 + (i % 5))),
                place_of_birth="Lagos",
                class_on_entry=str(classroom),
                date_of_entry=now.date(),
                father_name="Demo Father",
                mother_name="Demo Mother",
                class_at_present=str(classroom),
                classroom=classroom,
            )
            created_students.append(s)

        students = list(Student.objects.filter(classroom=classroom).order_by("surname")[:num_students])

        # Create assessments: CA and Exam for each subject
        math_ca, _ = Assessment.objects.get_or_create(
            assignment=assg_math,
            assessment_type=ca_type,
            title="Math CA 1",
            defaults={"date": now.date(), "max_score": 40, "created_by": teacher},
        )
        math_exam, _ = Assessment.objects.get_or_create(
            assignment=assg_math,
            assessment_type=exam_type,
            title="Math Exam",
            defaults={"date": now.date(), "max_score": 60, "created_by": teacher},
        )
        eng_ca, _ = Assessment.objects.get_or_create(
            assignment=assg_eng,
            assessment_type=ca_type,
            title="English CA 1",
            defaults={"date": now.date(), "max_score": 40, "created_by": teacher},
        )
        eng_exam, _ = Assessment.objects.get_or_create(
            assignment=assg_eng,
            assessment_type=exam_type,
            title="English Exam",
            defaults={"date": now.date(), "max_score": 60, "created_by": teacher},
        )

        # Enter scores with some variety
        import random

        for student in students:
            # Math
            StudentScore.objects.update_or_create(
                assessment=math_ca,
                student=student,
                defaults={"score": random.uniform(20, 40), "submitted_by": teacher},
            )
            StudentScore.objects.update_or_create(
                assessment=math_exam,
                student=student,
                defaults={"score": random.uniform(30, 60), "submitted_by": teacher},
            )

            # English
            StudentScore.objects.update_or_create(
                assessment=eng_ca,
                student=student,
                defaults={"score": random.uniform(15, 40), "submitted_by": teacher},
            )
            StudentScore.objects.update_or_create(
                assessment=eng_exam,
                student=student,
                defaults={"score": random.uniform(25, 60), "submitted_by": teacher},
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(students)} students with assessments and scores."))
        self.stdout.write(self.style.NOTICE("Next: calculate term results for analytics."))


