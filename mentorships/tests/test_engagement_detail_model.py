from django.core.exceptions import FieldDoesNotExist
from django.db import IntegrityError, models

from engagements.models import Engagement
from mentorships.models import (
    MentorshipApplication,
    MentorshipEngagement,
    MentorshipOffer,
)
from futaverse.tests_helpers import BaseAPITestCase


class MentorshipEngagementDetailTests(BaseAPITestCase):
    def setUp(self):
        self.student = self._create_student("stu@test.com")
        self.alumnus = self._create_alumnus("alum@test.com")
        self.mentorship = self.make_mentorship(alumnus_user=self.alumnus)

    def _make_engagement(self):
        return Engagement.objects.create(
            engagement_type=Engagement.EngagementType.MENTORSHIP,
            student=self.student.student_profile,
            alumnus=self.alumnus.alumni_profile,
        )

    def test_engagement_one_to_one_is_required(self):
        field = MentorshipEngagement._meta.get_field("engagement")
        self.assertFalse(field.null)

    def test_application_fk_is_protected_and_nullable(self):
        field = MentorshipEngagement._meta.get_field("application")
        self.assertTrue(field.null)
        self.assertEqual(field.remote_field.on_delete, models.PROTECT)

    def test_offer_fk_is_protected_and_nullable(self):
        field = MentorshipEngagement._meta.get_field("offer")
        self.assertTrue(field.null)
        self.assertEqual(field.remote_field.on_delete, models.PROTECT)

    def test_single_origin_constraint_exists(self):
        names = [c.name for c in MentorshipEngagement._meta.constraints]
        self.assertIn("mentorship_engagement_single_origin", names)

    def test_old_shared_fields_are_removed(self):
        for name in ("student", "alumnus", "source", "source_id", "status", "updated_at"):
            with self.assertRaises(FieldDoesNotExist):
                MentorshipEngagement._meta.get_field(name)

    def test_single_origin_constraint_rejects_both_origins(self):
        engagement = self._make_engagement()
        app = MentorshipApplication.objects.create(
            mentorship=self.mentorship,
            student=self.student.student_profile,
            cover_letter="x",
        )
        offer = MentorshipOffer.objects.create(
            mentorship=self.mentorship,
            student=self.student.student_profile,
        )
        with self.assertRaises(IntegrityError):
            MentorshipEngagement.objects.create(
                engagement=engagement,
                mentorship=self.mentorship,
                application=app,
                offer=offer,
            )
