from rest_framework import status

from internships.models import Internship, InternshipEngagement
from engagements.models import BaseEngagement
from futaverse.tests_helpers import BaseAPITestCase


class InternshipEngagementEndpointTests(BaseAPITestCase):
    def setUp(self):
        self.alumnus = self._create_alumnus("alum@test.com")
        self.other_alumnus = self._create_alumnus("other@test.com", firstname="Other")
        self.student = self._create_student("stu@test.com")
        self.other_student = self._create_student("otherstu@test.com")

        self.internship = Internship.objects.create(
            alumnus=self.alumnus.alumni_profile,
            title="SE Intern", description="desc", work_mode="Remote",
            engagement_type="Full-time", location="Lagos", duration_weeks=12,
            start_date="2026-01-01", end_date="2026-03-31",
            is_paid=True, stipend=100000, levels=[300],
            company="TC", company_type="Tech", industry="Tech",
            available_slots=5, remaining_slots=5,
        )

        self.engagement = InternshipEngagement.objects.create(
            internship=self.internship,
            student=self.student.student_profile,
            alumnus=self.alumnus.alumni_profile,
            source=InternshipEngagement.Source.APPLICATION,
            source_id=1,
            status=BaseEngagement.EngagementStatus.ACTIVE,
        )

    # --- LIST ---
    def test_alumnus_lists_own_engagements(self):
        headers = self._auth_header(self.alumnus)
        resp = self.client.get("/api/internships/engagements", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_student_lists_own_engagements(self):
        headers = self._auth_header(self.student)
        resp = self.client.get("/api/internships/engagements", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_student_does_not_see_other_engagements(self):
        headers = self._auth_header(self.other_student)
        resp = self.client.get("/api/internships/engagements", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)

    # --- RETRIEVE ---
    def test_owner_retrieves_engagement(self):
        headers = self._auth_header(self.alumnus)
        resp = self.client.get(f"/api/internships/engagements/{self.engagement.sqid}", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["sqid"], self.engagement.sqid)

    def test_other_alumnus_gets_404_on_engagement(self):
        headers = self._auth_header(self.other_alumnus)
        resp = self.client.get(f"/api/internships/engagements/{self.engagement.sqid}", **headers)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_engagement_response_has_internship_info(self):
        headers = self._auth_header(self.alumnus)
        resp = self.client.get(f"/api/internships/engagements/{self.engagement.sqid}", **headers)
        self.assertIn("internship_info", resp.data)

    def test_engagement_response_has_student_info(self):
        headers = self._auth_header(self.alumnus)
        resp = self.client.get(f"/api/internships/engagements/{self.engagement.sqid}", **headers)
        self.assertIn("student_info", resp.data)

    # --- COMPLETE ---
    def test_alumnus_completes_engagement(self):
        headers = self._auth_header(self.alumnus)
        resp = self.client.patch(f"/api/internships/engagements/{self.engagement.sqid}/completed", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.engagement.refresh_from_db()
        self.assertEqual(self.engagement.status, BaseEngagement.EngagementStatus.COMPLETED)

    def test_other_alumnus_gets_404_on_complete(self):
        headers = self._auth_header(self.other_alumnus)
        resp = self.client.patch(f"/api/internships/engagements/{self.engagement.sqid}/completed", **headers)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_complete_non_active_engagement(self):
        self.engagement.status = BaseEngagement.EngagementStatus.COMPLETED
        self.engagement.save(update_fields=["status"])
        headers = self._auth_header(self.alumnus)
        resp = self.client.patch(f"/api/internships/engagements/{self.engagement.sqid}/completed", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_cannot_complete_engagement(self):
        headers = self._auth_header(self.student)
        resp = self.client.patch(f"/api/internships/engagements/{self.engagement.sqid}/completed", **headers)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # --- ACKNOWLEDGE ---
    def test_student_acknowledges_completed_engagement(self):
        self.engagement.status = BaseEngagement.EngagementStatus.COMPLETED
        self.engagement.save(update_fields=["status"])
        headers = self._auth_header(self.student)
        resp = self.client.patch(f"/api/internships/engagements/{self.engagement.sqid}/acknowledged", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.engagement.refresh_from_db()
        self.assertEqual(self.engagement.status, BaseEngagement.EngagementStatus.ACKNOWLEDGED)

    def test_alumnus_cannot_acknowledge_engagement(self):
        headers = self._auth_header(self.alumnus)
        resp = self.client.patch(f"/api/internships/engagements/{self.engagement.sqid}/acknowledged", **headers)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
