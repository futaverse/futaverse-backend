from datetime import date

from django.test import TestCase
from django.utils import timezone

from engagements.models import EngagementLifecycleStatus
from internships.models import (
    Internship,
    InternshipApplication,
    InternshipOffer,
)
from core.models import User, StudentProfile, AlumniProfile


def _create_student():
    user = User.objects.create_user(
        email="student@test.com",
        password="testpass123",
        role=User.Role.STUDENT,
        is_active=True,
    )
    profile = StudentProfile.objects.create(
        user=user,
        phone_num="08012345678",
        gender="male",
        firstname="Test",
        lastname="Student",
        address="123 Test St",
        state="Lagos",
        country="Nigeria",
        department="Computer Science",
        faculty="Engineering",
        level=300,
        cgpa=4.50,
        skills=["python"],
        expected_grad_year="2027",
    )
    return profile


def _create_alumnus():
    user = User.objects.create_user(
        email="alumnus@test.com",
        password="testpass123",
        role=User.Role.ALUMNI,
        is_active=True,
    )
    profile = AlumniProfile.objects.create(
        user=user,
        phone_num="08098765432",
        gender="male",
        firstname="Test",
        lastname="Alumnus",
        address="456 Test Ave",
        state="Ogun",
        country="Nigeria",
        department="Computer Science",
        faculty="Engineering",
        grad_year="2020",
        current_job_title="Software Engineer",
        current_company="Tech Corp",
        industry="Technology",
        years_of_exp=5,
    )
    return profile


def _create_internship(alumnus):
    return Internship.objects.create(
        alumnus=alumnus,
        title="Test Internship",
        description="A test internship",
        work_mode=Internship.WorkMode.REMOTE,
        engagement_type=Internship.EngagementType.FULL_TIME,
        location="Lagos",
        duration_weeks=12,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        company="Test Corp",
        company_type="Startup",
        industry="Technology",
    )


class EngagementLifecycleTests(TestCase):
    def setUp(self):
        self.student = _create_student()
        self.alumnus = _create_alumnus()
        self.internship = _create_internship(self.alumnus)

    def test_application_default_status_is_pending(self):
        app = InternshipApplication.objects.create(
            internship=self.internship,
            student=self.student,
        )
        self.assertEqual(app.status, EngagementLifecycleStatus.PENDING)

    def test_application_accept_sets_accepted_and_responded_at(self):
        app = InternshipApplication.objects.create(
            internship=self.internship,
            student=self.student,
        )
        app.accept()
        app.refresh_from_db()
        self.assertEqual(app.status, EngagementLifecycleStatus.ACCEPTED)
        self.assertIsNotNone(app.responded_at)
        self.assertTrue(app.responded_at <= timezone.now())

    def test_application_reject_sets_rejected_and_responded_at(self):
        app = InternshipApplication.objects.create(
            internship=self.internship,
            student=self.student,
        )
        app.reject()
        app.refresh_from_db()
        self.assertEqual(app.status, EngagementLifecycleStatus.REJECTED)
        self.assertIsNotNone(app.responded_at)
        self.assertTrue(app.responded_at <= timezone.now())

    def test_application_withdraw_sets_withdrawn(self):
        app = InternshipApplication.objects.create(
            internship=self.internship,
            student=self.student,
        )
        app.withdraw()
        app.refresh_from_db()
        self.assertEqual(app.status, EngagementLifecycleStatus.WITHDRAWN)

    def test_offer_default_status_is_pending(self):
        offer = InternshipOffer.objects.create(
            internship=self.internship,
            student=self.student,
        )
        self.assertEqual(offer.status, EngagementLifecycleStatus.PENDING)

    def test_offer_accept_sets_accepted_and_responded_at(self):
        offer = InternshipOffer.objects.create(
            internship=self.internship,
            student=self.student,
        )
        offer.accept()
        offer.refresh_from_db()
        self.assertEqual(offer.status, EngagementLifecycleStatus.ACCEPTED)
        self.assertIsNotNone(offer.responded_at)
        self.assertTrue(offer.responded_at <= timezone.now())

    def test_offer_reject_sets_rejected_and_responded_at(self):
        offer = InternshipOffer.objects.create(
            internship=self.internship,
            student=self.student,
        )
        offer.reject()
        offer.refresh_from_db()
        self.assertEqual(offer.status, EngagementLifecycleStatus.REJECTED)
        self.assertIsNotNone(offer.responded_at)
        self.assertTrue(offer.responded_at <= timezone.now())

    def test_offer_withdraw_sets_withdrawn(self):
        offer = InternshipOffer.objects.create(
            internship=self.internship,
            student=self.student,
        )
        offer.withdraw()
        offer.refresh_from_db()
        self.assertEqual(offer.status, EngagementLifecycleStatus.WITHDRAWN)
