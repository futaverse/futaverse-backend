from django.db import models
from django.test import TestCase

from internships.models import Internship, InternshipApplication, ApplicationResume
from futaverse.tests_helpers import BaseAPITestCase


class InternshipModelTests(BaseAPITestCase):
    def test_company_has_max_length(self):
        """B5: company CharField must define max_length."""
        field = Internship._meta.get_field("company")
        self.assertIsNotNone(field.max_length)

    def test_company_type_has_max_length(self):
        """B5: company_type CharField must define max_length."""
        field = Internship._meta.get_field("company_type")
        self.assertIsNotNone(field.max_length)

    def test_application_responded_at_not_auto_now(self):
        """B7: responded_at must NOT have auto_now (only set on status change)."""
        field = InternshipApplication._meta.get_field("responded_at")
        self.assertFalse(field.auto_now)

    def test_application_responded_at_nullable(self):
        """B7: responded_at must be nullable (starts null, set on first transition)."""
        field = InternshipApplication._meta.get_field("responded_at")
        self.assertTrue(field.null)


class ApplicationResumeStrTests(TestCase):
    def test_str_without_application_does_not_crash(self):
        """B10: __str__ must not crash when application is None."""
        from core.models import StudentProfile, User
        user = User.objects.create_user(
            email="resume@test.com", password="pass", role=User.Role.STUDENT, is_active=True
        )
        profile = StudentProfile.objects.create(
            user=user, phone_num="08000000000", gender="male",
            firstname="Resume", lastname="Test",
            address="Addr", state="LA", country="NG",
            department="CS", faculty="Eng", level=300, cgpa=3.0,
            skills=[], expected_grad_year="2027",
        )
        resume = ApplicationResume.objects.create(
            student=profile, resume="http://example.com/resume.pdf"
        )
        # Should not raise
        str(resume)
