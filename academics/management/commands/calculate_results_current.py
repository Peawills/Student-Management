from django.core.management.base import BaseCommand
from django.db.models import Avg, Max, Min
from django.db import transaction
from django.utils import timezone

from academics.models import Term, ClassRoom, SubjectAssignment, Assessment, StudentScore, TermResult


class Command(BaseCommand):
    help = "Calculate term results for all classes in the current term (demo helper)."

    def handle(self, *args, **options):
        term = Term.objects.filter(is_current=True).first()
        if not term:
            self.stdout.write(self.style.ERROR("No current term found."))
            return

        classrooms = ClassRoom.objects.filter(session__is_current=True)
        total_results = 0

        with transaction.atomic():
            for classroom in classrooms:
                assignments = SubjectAssignment.objects.filter(classroom=classroom, term=term)
                students = classroom.students.all()

                for assignment in assignments:
                    assessments = Assessment.objects.filter(assignment=assignment)

                    for student in students:
                        ca_scores = StudentScore.objects.filter(
                            assessment__in=assessments.exclude(assessment_type__code="EXAM"),
                            student=student,
                        )
                        ca_total = sum(
                            (s.score / s.assessment.max_score) * s.assessment.assessment_type.weight
                            for s in ca_scores
                            if s.score is not None
                        )

                        exam_assessment = assessments.filter(assessment_type__code="EXAM").first()
                        exam_score = 0
                        if exam_assessment:
                            exam_score_obj = StudentScore.objects.filter(
                                assessment=exam_assessment, student=student
                            ).first()
                            if exam_score_obj and exam_assessment.max_score:
                                exam_score = (exam_score_obj.score / exam_assessment.max_score) * 60

                        term_result, created = TermResult.objects.update_or_create(
                            student=student,
                            subject=assignment.subject,
                            term=term,
                            classroom=classroom,
                            defaults={
                                "ca_total": ca_total,
                                "exam_score": exam_score,
                            },
                        )
                        total_results += 1 if created else 0

                    # After creating results for this subject, update class stats and positions
                    subject_results = TermResult.objects.filter(
                        subject=assignment.subject, term=term, classroom=classroom
                    )
                    if subject_results.exists():
                        stats = subject_results.aggregate(
                            avg=Avg("total_score"),
                            max_score=Max("total_score"),
                            min_score=Min("total_score"),
                        )
                        subject_results.update(
                            class_average=stats["avg"],
                            highest_score=stats["max_score"],
                            lowest_score=stats["min_score"],
                        )
                        for position, result in enumerate(subject_results.order_by("-total_score"), start=1):
                            result.position = position
                            result.save(update_fields=["position"])

        self.stdout.write(self.style.SUCCESS(f"Calculated/updated results. New results created: {total_results}"))


