# c:\Users\Williams Peaceful\Portfolio\Djangoproject\Studentmanagement\portal\tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta

from records.models import Student
from academics.models import (
    AcademicSession,
    Term,
    ClassRoom,
    Subject,
    SubjectAssignment,
    AssessmentType,
    Assessment,
    StudentScore,
    ReportCard,
)
from portal.models import ParentProfile, StudentProfile, Announcement, PortalMessage
from portal.forms import (
    UserProfileForm,
    ParentProfileForm,
    PortalMessageForm,
    CustomPasswordChangeForm,
)


class PortalTestCase(TestCase):
    """Base test case for portal app with common setup."""

    @classmethod
    def setUpTestData(cls):
        # Create a staff user (admin)
        cls.staff_user = User.objects.create_user(
            username="staffuser",
            password="password",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )

        # Create an academic session and term
        cls.session = AcademicSession.objects.create(
            name="2024/2025",
            start_date="2024-09-01",
            end_date="2025-07-31",
            is_current=True,
        )
        cls.term = Term.objects.create(
            session=cls.session,
            name="First",
            start_date="2024-09-01",
            end_date="2024-12-15",
            is_current=True,
        )

        # Create a classroom
        cls.classroom = ClassRoom.objects.create(
            level="JSS1", arm="A", session=cls.session, class_teacher=cls.staff_user
        )

        # Create a student and associated portal user/profile
        # The signal will create the User and StudentProfile automatically
        cls.student_obj = Student.objects.create(
            surname="Doe",
            other_name="John",
            admission_no="2024-001",
            sex="Male",
            date_of_birth="2010-01-01",
            residential_address="123 Student St",
            nationality="Nigerian",
            state_of_origin="Lagos",
            lga="Ikeja",
            class_on_entry="JSS1",
            date_of_entry="2024-09-01",
            classroom=cls.classroom,
            father_name="John Doe Sr.",
            father_mobile="08012345678",
            mother_name="Jane Doe",
            mother_mobile="08087654321",
        )
        cls.student_user = cls.student_obj.user  # Linked by signal
        cls.student_profile = cls.student_user.student_profile  # Linked by signal

        # Create a parent user and profile, linked to the student
        cls.parent_user = User.objects.create_user(
            username="parentuser",
            password="password",
            first_name="Jane",
            last_name="Doe",
        )
        cls.parent_profile = ParentProfile.objects.create(
            user=cls.parent_user,
            phone_number="08011223344",
            relationship="Mother",
        )
        cls.parent_profile.students.add(cls.student_obj)

        # Create another student and parent for testing permissions
        cls.other_student_obj = Student.objects.create(
            surname="Smith",
            other_name="Alice",
            admission_no="2024-002",
            sex="Female",
            date_of_birth="2011-03-15",
            residential_address="456 Other St",
            nationality="Nigerian",
            state_of_origin="Ogun",
            lga="Abeokuta",
            class_on_entry="JSS1",
            date_of_entry="2024-09-01",
            classroom=cls.classroom,
            father_name="Bob Smith",
            father_mobile="09012345678",
            mother_name="Carol Smith",
            mother_mobile="09087654321",
        )
        cls.other_student_user = cls.other_student_obj.user
        cls.other_parent_user = User.objects.create_user(
            username="otherparent",
            password="password",
            first_name="Carol",
            last_name="Smith",
        )
        cls.other_parent_profile = ParentProfile.objects.create(
            user=cls.other_parent_user,
            phone_number="09011223344",
            relationship="Mother",
        )
        cls.other_parent_profile.students.add(cls.other_student_obj)

        # Create some academic data for the student
        cls.subject = Subject.objects.create(name="Mathematics", code="MATH101")
        cls.assignment = SubjectAssignment.objects.create(
            classroom=cls.classroom,
            subject=cls.subject,
            teacher=cls.staff_user,
            term=cls.term,
        )
        cls.assessment_type = AssessmentType.objects.create(
            name="Test", code="TEST", weight=40
        )
        cls.assessment = Assessment.objects.create(
            assignment=cls.assignment,
            assessment_type=cls.assessment_type,
            title="Mid-Term Test",
            date="2024-10-20",
            max_score=50,
            created_by=cls.staff_user,
        )
        StudentScore.objects.create(
            assessment=cls.assessment,
            student=cls.student_obj,
            score=45,
            submitted_by=cls.staff_user,
        )
        # Create a report card
        ReportCard.objects.create(
            student=cls.student_obj,
            term=cls.term,
            classroom=cls.classroom,
            total_score=80,
            average_score=80,
            position=1,
            out_of=1,
            is_published=True,
        )

        # Create announcements
        cls.announcement_all = Announcement.objects.create(
            title="General Holiday",
            content="School will be closed next week.",
            target_audience="All",
            created_by=cls.staff_user,
            is_active=True,
        )
        cls.announcement_parents = Announcement.objects.create(
            title="Parent-Teacher Meeting",
            content="Meeting details...",
            target_audience="Parents",
            created_by=cls.staff_user,
            is_active=True,
        )
        cls.announcement_students = Announcement.objects.create(
            title="Exam Schedule",
            content="Exams start on Monday.",
            target_audience="Students",
            created_by=cls.staff_user,
            is_active=True,
        )

        # Create messages
        cls.message_to_parent = PortalMessage.objects.create(
            sender=cls.staff_user,
            recipient=cls.parent_user,
            student=cls.student_obj,
            subject="Regarding John Doe's progress",
            message="John is doing well.",
        )
        cls.message_to_student = PortalMessage.objects.create(
            sender=cls.staff_user,
            recipient=cls.student_user,
            student=cls.student_obj,
            subject="Good work on test",
            message="Keep it up!",
        )

    def setUp(self):
        self.client = Client()

    def test_portal_dashboard_redirection(self):
        # Test staff user redirection
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.get(reverse("portal:dashboard"))
        self.assertRedirects(response, reverse("records:admin_dashboard"))

        # Test student user redirection
        self.client.login(username=self.student_user.username, password="password")
        response = self.client.get(reverse("portal:dashboard"))
        self.assertRedirects(response, reverse("portal:student_dashboard"))

        # Test parent user redirection
        self.client.login(username=self.parent_user.username, password="password")
        response = self.client.get(reverse("portal:dashboard"))
        self.assertRedirects(response, reverse("portal:parent_dashboard"))

        # Test unauthenticated user redirection to login
        self.client.logout()
        response = self.client.get(reverse("portal:dashboard"))
        self.assertRedirects(
            response, reverse("accounts:login") + "?next=/portal/dashboard/"
        )

        # Test a regular user (not staff, student, or parent)
        regular_user = User.objects.create_user(username="regular", password="password")
        self.client.login(username="regular", password="password")
        response = self.client.get(reverse("portal:dashboard"))
        self.assertRedirects(
            response, reverse("accounts:login")
        )  # Should redirect to login with error message
        self.assertIn(
            "You do not have a portal profile.",
            self.client.session["_messages"]._loaded_messages[0].message,
        )

    def test_student_dashboard(self):
        self.client.login(username=self.student_user.username, password="password")
        response = self.client.get(reverse("portal:student_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "portal/student_dashboard.html")
        self.assertContains(response, self.student_obj.full_name)
        self.assertContains(response, self.student_obj.admission_no)
        self.assertContains(response, self.announcement_all.title)
        self.assertContains(response, self.announcement_students.title)
        self.assertNotContains(
            response, self.announcement_parents.title
        )  # Should not see parent-only announcement
        self.assertContains(response, self.assessment.title)  # Recent grade
        self.assertContains(
            response, "You have no upcoming assignments."
        )  # Assuming no upcoming assignments in setup

    def test_student_scores_view(self):
        self.client.login(username=self.student_user.username, password="password")
        response = self.client.get(reverse("portal:student_scores"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "portal/student_scores.html")
        self.assertContains(response, self.student_obj.full_name)
        self.assertContains(response, self.assessment.title)
        self.assertContains(response, "45.0/50")

    def test_student_reports_view(self):
        self.client.login(username=self.student_user.username, password="password")
        response = self.client.get(reverse("portal:student_reports"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "portal/student_reports.html")
        self.assertContains(response, self.student_obj.full_name)
        self.assertContains(response, self.term.name)
        self.assertContains(response, "80.0")  # Average score from report card

    # Add tests for student_attendance and student_timetable similarly
    def test_parent_dashboard(self):
        self.client.login(username=self.parent_user.username, password="password")
        response = self.client.get(reverse("portal:parent_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "portal/parent_dashboard.html")
        self.assertContains(response, self.student_obj.full_name)
        self.assertContains(response, self.announcement_all.title)
        self.assertContains(response, self.announcement_parents.title)
        self.assertNotContains(
            response, self.announcement_students.title
        )  # Should not see student-only announcement

    def test_parent_student_detail_access(self):
        self.client.login(username=self.parent_user.username, password="password")
        response = self.client.get(
            reverse("portal:parent_student_detail", args=[self.student_obj.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student_obj.full_name)

        # Test parent trying to access another parent's child
        response = self.client.get(
            reverse("portal:parent_student_detail", args=[self.other_student_obj.id])
        )
        self.assertRedirects(response, reverse("portal:parent_dashboard"))
        self.assertIn(
            "Access denied.",
            self.client.session["_messages"]._loaded_messages[0].message,
        )

    # Add tests for parent_student_scores, parent_student_attendance, parent_student_reports, parent_timetable, parent_fees similarly
    def test_update_profile_student(self):
        self.client.login(username=self.student_user.username, password="password")
        response = self.client.post(
            reverse("portal:update_profile"),
            {
                "first_name": "Johnny",
                "last_name": "Doe",
                "email": "johnny.doe@example.com",
            },
        )
        self.assertRedirects(response, reverse("portal:profile"))
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.first_name, "Johnny")
        self.assertEqual(self.student_user.email, "johnny.doe@example.com")

    def test_update_profile_parent(self):
        self.client.login(username=self.parent_user.username, password="password")
        response = self.client.post(
            reverse("portal:update_profile"),
            {
                "first_name": "Janet",
                "last_name": "Doe",
                "email": "janet.doe@example.com",
                "phone_number": "09098765432",
                "address": "New Parent Address",
                "occupation": "Engineer",
            },
        )
        self.assertRedirects(response, reverse("portal:profile"))
        self.parent_user.refresh_from_db()
        self.parent_profile.refresh_from_db()
        self.assertEqual(self.parent_user.first_name, "Janet")
        self.assertEqual(self.parent_profile.phone_number, "09098765432")

    def test_change_password(self):
        self.client.login(username=self.student_user.username, password="password")
        response = self.client.post(
            reverse("portal:change_password"),
            {
                "old_password": "password",
                "new_password1": "new_secure_password",
                "new_password2": "new_secure_password",
            },
        )
        self.assertRedirects(response, reverse("portal:profile"))
        self.student_user.refresh_from_db()
        self.assertTrue(self.student_user.check_password("new_secure_password"))

        # Test with incorrect old password
        self.client.login(
            username=self.student_user.username, password="new_secure_password"
        )
        response = self.client.post(
            reverse("portal:change_password"),
            {
                "old_password": "wrong_password",
                "new_password1": "another_new_password",
                "new_password2": "another_new_password",
            },
        )
        self.assertEqual(response.status_code, 200)  # Form should re-render with errors
        self.assertContains(response, "Your old password was entered incorrectly.")

    def test_compose_message_student_to_staff(self):
        self.client.login(username=self.student_user.username, password="password")
        response = self.client.post(
            reverse("portal:compose_message"),
            {
                "recipient": self.staff_user.id,
                "subject": "Question about homework",
                "message": "I need help with problem 3.",
            },
        )
        self.assertRedirects(response, reverse("portal:messages_inbox"))
        self.assertTrue(
            PortalMessage.objects.filter(
                sender=self.student_user, recipient=self.staff_user
            ).exists()
        )
        # Check that student field is automatically set for student sender
        message = PortalMessage.objects.get(
            sender=self.student_user, recipient=self.staff_user
        )
        self.assertEqual(message.student, self.student_obj)

    def test_compose_message_parent_to_staff_about_child(self):
        self.client.login(username=self.parent_user.username, password="password")
        response = self.client.post(
            reverse("portal:compose_message"),
            {
                "recipient": self.staff_user.id,
                "student": self.student_obj.id,  # Parent specifies child
                "subject": "Inquiry about John's grades",
                "message": "Could you provide an update?",
            },
        )
        self.assertRedirects(response, reverse("portal:messages_inbox"))
        self.assertTrue(
            PortalMessage.objects.filter(
                sender=self.parent_user,
                recipient=self.staff_user,
                student=self.student_obj,
            ).exists()
        )

    def test_messages_inbox(self):
        self.client.login(username=self.parent_user.username, password="password")
        response = self.client.get(reverse("portal:messages_inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.message_to_parent.subject)
        self.assertContains(response, "1 New")  # One unread message

    def test_message_detail_marks_as_read(self):
        self.client.login(username=self.parent_user.username, password="password")
        self.assertFalse(self.message_to_parent.is_read)
        response = self.client.get(
            reverse("portal:message_detail", args=[self.message_to_parent.id])
        )
        self.assertEqual(response.status_code, 200)
        self.message_to_parent.refresh_from_db()
        self.assertTrue(self.message_to_parent.is_read)
        self.assertIsNotNone(self.message_to_parent.read_at)

    def test_reply_message(self):
        self.client.login(username=self.parent_user.username, password="password")
        response = self.client.post(
            reverse("portal:reply_message", args=[self.message_to_parent.id]),
            {"message": "Thanks for the update!"},
        )
        self.assertRedirects(
            response, reverse("portal:message_detail", args=[self.message_to_parent.id])
        )
        reply = PortalMessage.objects.filter(
            parent_message=self.message_to_parent
        ).first()
        self.assertIsNotNone(reply)
        self.assertEqual(reply.sender, self.parent_user)
        self.assertEqual(reply.recipient, self.staff_user)
        self.assertTrue(reply.subject.startswith("Re:"))

    def test_announcements_list_student(self):
        self.client.login(username=self.student_user.username, password="password")
        response = self.client.get(reverse("portal:announcements_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.announcement_all.title)
        self.assertContains(response, self.announcement_students.title)
        self.assertNotContains(response, self.announcement_parents.title)

    def test_announcements_list_parent(self):
        self.client.login(username=self.parent_user.username, password="password")
        response = self.client.get(reverse("portal:announcements_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.announcement_all.title)
        self.assertContains(response, self.announcement_parents.title)
        self.assertNotContains(response, self.announcement_students.title)

    def test_announcement_detail(self):
        self.client.login(username=self.student_user.username, password="password")
        response = self.client.get(
            reverse("portal:announcement_detail", args=[self.announcement_all.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.announcement_all.title)
        self.assertContains(response, self.announcement_all.content)
