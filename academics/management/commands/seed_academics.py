from django.core.management.base import BaseCommand
from academics.models import AcademicSession, Term
from django.utils import timezone


class Command(BaseCommand):
    help = "Create a sample AcademicSession and Term if none exist"

    def handle(self, *args, **options):
        now = timezone.now()
        year = now.year
        session_name = f"{year}/{year + 1}"

        if AcademicSession.objects.exists():
            self.stdout.write(
                self.style.NOTICE("AcademicSession(s) already exist. Skipping.")
            )
            return

        session = AcademicSession.objects.create(
            name=session_name,
            start_date=now.date(),
            end_date=now.date(),
            is_current=True,
        )
        Term.objects.create(
            session=session,
            name="First",
            start_date=now.date(),
            end_date=now.date(),
            is_current=True,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Created sample session {session_name} and First term.")
        )
