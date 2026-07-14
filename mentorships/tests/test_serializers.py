from rest_framework import status

from mentorships.models import (
    Mentorship, MentorshipApplication, MentorshipOffer,
    MentorshipEngagement,
)
from engagements.models import EngagementLifecycleStatus
from mentorships.models import MentorshipCategory, FocusArea
from futaverse.tests_helpers import BaseAPITestCase


class MentorshipFlowTests(BaseAPITestCase):
    """B1 + B9: Serializer authorization and validation tests."""

    def setUp(self):
        self.alumnus = self._create_alumnus("alumnus@test.com")
        self.other_alumnus = self._create_alumnus("other@test.com", firstname="Other")
        self.student = self._create_student("student@test.com")

        self.mentorship = Mentorship.objects.create(
            alumnus=self.alumnus.alumni_profile,
            title="Career Mentorship",
            description="Guidance for new grads",
            category=MentorshipCategory.CAREER_DEVELOPMENT,
            focus_areas=["career_guidance", "cv_and_portfolio"],
            work_mode="Remote",
            duration_weeks=8,
            start_date="2026-01-01",
            end_date="2026-02-28",
            available_slots=3,
            remaining_slots=3,
            is_active=True,
        )

    # B1: Alumnus can accept/reject/withdraw without crash
    def test_alumnus_accept_application_returns_201(self):
        app = MentorshipApplication.objects.create(
            mentorship=self.mentorship,
            student=self.student.student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(
            f"/api/mentorships/applications/{app.sqid}/accept",
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_alumnus_reject_application_returns_200(self):
        app = MentorshipApplication.objects.create(
            mentorship=self.mentorship,
            student=self.student.student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(
            f"/api/mentorships/applications/{app.sqid}/reject",
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_alumnus_withdraw_offer_returns_200(self):
        offer = MentorshipOffer.objects.create(
            mentorship=self.mentorship,
            student=self.student.student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(
            f"/api/mentorships/offers/{offer.sqid}/withdraw",
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # B9: Mentorship application validation
    def test_cannot_apply_to_inactive_mentorship(self):
        self.mentorship.is_active = False
        self.mentorship.save(update_fields=["is_active"])
        headers = self._auth_header(self.student)
        resp = self.client.post(
            "/api/mentorships/application",
            {"mentorship": self.mentorship.sqid, "cover_letter": "I want to join"},
            **headers,
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_apply_twice_to_same_mentorship(self):
        headers = self._auth_header(self.student)
        self.client.post(
            "/api/mentorships/application",
            {"mentorship": self.mentorship.sqid, "cover_letter": "First app"},
            **headers,
            format="json",
        )
        resp = self.client.post(
            "/api/mentorships/application",
            {"mentorship": self.mentorship.sqid, "cover_letter": "Duplicate"},
            **headers,
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
