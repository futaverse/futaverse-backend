from rest_framework import status

from internships.models import (
    Internship, InternshipEngagement,
)
from engagements.models import BaseEngagement
from futaverse.tests_helpers import BaseAPITestCase


class EngagementViewTests(BaseAPITestCase):
    """B2 + B3: Engagement ownership and stale response tests."""

    def setUp(self):
        self.alumnus = self._create_alumnus("alumnus@test.com")
        self.other_alumnus = self._create_alumnus("other@test.com", firstname="Other")
        self.student = self._create_student("student@test.com")
        self.other_student = self._create_student("other_s@test.com")

        self.internship = Internship.objects.create(
            alumnus=self.alumnus.alumni_profile,
            title="SE Intern",
            description="...",
            work_mode="Remote",
            engagement_type="Full-time",
            location="Remote",
            duration_weeks=12,
            start_date="2026-01-01",
            end_date="2026-03-31",
            is_paid=True,
            stipend=100000,
            levels=[300],
            company="Tech Corp",
            company_type="Technology",
            industry="Technology",
            available_slots=5,
            remaining_slots=5,
        )

        self.engagement = InternshipEngagement.objects.create(
            internship=self.internship,
            student=self.student.student_profile,
            alumnus=self.alumnus.alumni_profile,
            source=InternshipEngagement.Source.APPLICATION,
            source_id=1,
            status=BaseEngagement.EngagementStatus.ACTIVE,
        )

    def test_other_alumnus_cannot_complete_engagement(self):
        """B2: Other alumnus cannot mark engagement as completed."""
        headers = self._auth_header(self.other_alumnus)
        resp = self.client.patch(
            f"/api/internships/engagements/{self.engagement.sqid}/completed",
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_other_student_cannot_acknowledge_engagement(self):
        """B2: Other student cannot acknowledge engagement."""
        headers = self._auth_header(self.other_student)
        resp = self.client.patch(
            f"/api/internships/engagements/{self.engagement.sqid}/acknowledged",
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_completed_response_shows_completed_status(self):
        """B3: Response after marking complete must show 'completed', not 'active'."""
        headers = self._auth_header(self.alumnus)
        resp = self.client.patch(
            f"/api/internships/engagements/{self.engagement.sqid}/completed",
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], BaseEngagement.EngagementStatus.COMPLETED)
