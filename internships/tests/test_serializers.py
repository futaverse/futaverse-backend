from rest_framework import status

from internships.models import (
    Internship, InternshipApplication, InternshipOffer,
    InternshipEngagement,
)
from engagements.models import EngagementLifecycleStatus
from futaverse.tests_helpers import BaseAPITestCase


class InternshipApplicationFlowTests(BaseAPITestCase):
    """B1: Serializers must not crash for alumnus users."""

    def setUp(self):
        self.alumnus = self._create_alumnus("alumnus@test.com")
        self.other_alumnus = self._create_alumnus("other@test.com", firstname="Other")
        self.student = self._create_student("student@test.com")

        self.internship = Internship.objects.create(
            alumnus=self.alumnus.alumni_profile,
            title="Software Engineer Intern",
            description="Great opportunity",
            work_mode="Remote",
            engagement_type="Full-time",
            location="Remote",
            duration_weeks=12,
            start_date="2026-01-01",
            end_date="2026-03-31",
            is_paid=True,
            stipend=100000,
            levels=[300, 400],
            company="Tech Corp",
            company_type="Technology",
            industry="Technology",
            available_slots=5,
            remaining_slots=5,
        )

    def test_alumnus_accept_application_returns_201(self):
        """B1: Alumnus accepting an application must not crash (returns 201)."""
        app = InternshipApplication.objects.create(
            internship=self.internship,
            student=self.student.student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(
            f"/api/internships/applications/{app.sqid}/accept",
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_alumnus_reject_application_returns_200(self):
        """B1: Alumnus rejecting an application must not crash (returns 200)."""
        app = InternshipApplication.objects.create(
            internship=self.internship,
            student=self.student.student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(
            f"/api/internships/applications/{app.sqid}/reject",
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_alumnus_withdraw_offer_returns_200(self):
        """B1: Alumnus withdrawing an offer must not crash (returns 200)."""
        offer = InternshipOffer.objects.create(
            internship=self.internship,
            student=self.student.student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(
            f"/api/internships/offers/{offer.sqid}/withdraw",
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_other_alumnus_cannot_accept_application(self):
        """B6: Alumnus cannot accept an application for another alumnus's internship."""
        app = InternshipApplication.objects.create(
            internship=self.internship,
            student=self.student.student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )
        headers = self._auth_header(self.other_alumnus)
        resp = self.client.post(
            f"/api/internships/applications/{app.sqid}/accept",
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_alumnus_cannot_create_offer(self):
        """B6: Alumnus cannot create an offer for another alumnus's internship."""
        headers = self._auth_header(self.other_alumnus)
        resp = self.client.post(
            "/api/internships/offer",
            {"internship": self.internship.sqid, "student": self.student.student_profile.sqid},
            **headers,
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_accept_offer_still_works(self):
        """B1: Student accepting an offer must still work (regression)."""
        offer = InternshipOffer.objects.create(
            internship=self.internship,
            student=self.student.student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )
        headers = self._auth_header(self.student)
        resp = self.client.post(
            f"/api/internships/offers/{offer.sqid}/accept",
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_student_withdraw_application_still_works(self):
        """B1: Student withdrawing their application must still work (regression)."""
        app = InternshipApplication.objects.create(
            internship=self.internship,
            student=self.student.student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )
        headers = self._auth_header(self.student)
        resp = self.client.post(
            f"/api/internships/applications/{app.sqid}/withdraw",
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
