from django.core.exceptions import FieldDoesNotExist
from django.db import IntegrityError, models
from django.test import TestCase

from engagements.models import Engagement
from internships.models import Internship, InternshipApplication, InternshipOffer, InternshipEngagement
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

    def test_application_resume_nullable(self):
        """Applications may be created without a resume."""
        field = InternshipApplication._meta.get_field("resume")
        self.assertTrue(field.null)

    def test_application_resume_protected(self):
        """A resume referenced by an application can never be hard-deleted."""
        field = InternshipApplication._meta.get_field("resume")
        self.assertEqual(field.remote_field.on_delete, models.PROTECT)


class InternshipEngagementDetailTests(BaseAPITestCase):
    def test_engagement_one_to_one_is_required(self):
        field = InternshipEngagement._meta.get_field("engagement")
        self.assertFalse(field.null)

    def test_application_fk_is_protected_and_nullable(self):
        field = InternshipEngagement._meta.get_field("application")
        self.assertTrue(field.null)
        self.assertEqual(field.remote_field.on_delete, models.PROTECT)

    def test_offer_fk_is_protected_and_nullable(self):
        field = InternshipEngagement._meta.get_field("offer")
        self.assertTrue(field.null)
        self.assertEqual(field.remote_field.on_delete, models.PROTECT)

    def test_single_origin_constraint_exists(self):
        names = [c.name for c in InternshipEngagement._meta.constraints]
        self.assertIn("internship_engagement_single_origin", names)

    def test_old_shared_fields_are_removed(self):
        for name in ("student", "alumnus", "source", "source_id", "status", "updated_at"):
            with self.assertRaises(FieldDoesNotExist):
                InternshipEngagement._meta.get_field(name)

    def test_single_origin_constraint_rejects_both_origins(self):
        student = self._create_student("stu@test.com")
        alumnus = self._create_alumnus("alum@test.com")
        internship = self.make_internship(alumnus_user=alumnus)
        app = InternshipApplication.objects.create(internship=internship, student=student.student_profile)
        offer = InternshipOffer.objects.create(internship=internship, student=student.student_profile)
        engagement = Engagement.objects.create(
            engagement_type=Engagement.EngagementType.INTERNSHIP,
            student=student.student_profile,
            alumnus=alumnus.alumni_profile,
        )
        with self.assertRaises(IntegrityError):
            InternshipEngagement.objects.create(
                engagement=engagement,
                internship=internship,
                application=app,
                offer=offer,
            )
