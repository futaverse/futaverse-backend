from rest_framework import status

from internships.models import Internship, InternshipApplication, InternshipEngagement
from engagements.models import EngagementLifecycleStatus
from futaverse.tests_helpers import BaseAPITestCase


class InternshipApplicationEndpointTests(BaseAPITestCase):
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
            require_resume=False,
        )

    def _create_application(self, student=None, internship=None):
        return InternshipApplication.objects.create(
            internship=internship or self.internship,
            student=(student or self.student).student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )

    # --- CREATE ---
    def test_student_can_apply(self):
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/internships/application", {
            "internship": self.internship.sqid,
            "cover_letter": "I want this",
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("sqid", resp.data)
        self.assertEqual(resp.data["status"], "pending")

    def test_apply_without_cover_letter_still_works(self):
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/internships/application", {
            "internship": self.internship.sqid,
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_cannot_apply_to_inactive_internship(self):
        self.internship.is_active = False
        self.internship.save(update_fields=["is_active"])
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/internships/application", {
            "internship": self.internship.sqid,
            "cover_letter": "test",
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_apply_twice(self):
        headers = self._auth_header(self.student)
        self.client.post("/api/internships/application", {"internship": self.internship.sqid}, **headers, format="json")
        resp = self.client.post("/api/internships/application", {"internship": self.internship.sqid}, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_apply_to_soft_deleted_internship(self):
        self.internship.soft_delete()
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/internships/application", {
            "internship": self.internship.sqid,
            "cover_letter": "test",
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_alumnus_cannot_apply(self):
        headers = self._auth_header(self.alumnus)
        resp = self.client.post("/api/internships/application", {
            "internship": self.internship.sqid,
            "cover_letter": "test",
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_apply(self):
        resp = self.client.post("/api/internships/application", {"internship": self.internship.sqid}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- LIST ---
    def test_alumnus_sees_applications_for_own_internship(self):
        self._create_application()
        headers = self._auth_header(self.alumnus)
        resp = self.client.get("/api/internships/applications", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_student_sees_own_applications(self):
        self._create_application()
        headers = self._auth_header(self.student)
        resp = self.client.get("/api/internships/applications", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_student_does_not_see_other_applications(self):
        self._create_application()  # student's application
        headers = self._auth_header(self.other_student)
        resp = self.client.get("/api/internships/applications", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)

    # --- RETRIEVE ---
    def test_student_retrieves_own_application(self):
        app = self._create_application()
        headers = self._auth_header(self.student)
        resp = self.client.get(f"/api/internships/applications/{app.sqid}", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["sqid"], app.sqid)

    def test_other_student_gets_404_on_application(self):
        app = self._create_application()
        headers = self._auth_header(self.other_student)
        resp = self.client.get(f"/api/internships/applications/{app.sqid}", **headers)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # --- ACCEPT ---
    def test_accept_returns_201_with_engagement(self):
        app = self._create_application()
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(f"/api/internships/applications/{app.sqid}/accept", **headers)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("engagement", resp.data)
        self.assertIn("sqid", resp.data["engagement"])

    def test_accept_decrements_remaining_slots(self):
        app = self._create_application()
        slots_before = self.internship.remaining_slots
        headers = self._auth_header(self.alumnus)
        self.client.post(f"/api/internships/applications/{app.sqid}/accept", **headers)
        self.internship.refresh_from_db()
        self.assertEqual(self.internship.remaining_slots, slots_before - 1)

    def test_accept_sets_application_status_to_accepted(self):
        app = self._create_application()
        headers = self._auth_header(self.alumnus)
        self.client.post(f"/api/internships/applications/{app.sqid}/accept", **headers)
        app.refresh_from_db()
        self.assertEqual(app.status, EngagementLifecycleStatus.ACCEPTED)

    def test_accept_sets_responded_at(self):
        app = self._create_application()
        headers = self._auth_header(self.alumnus)
        self.client.post(f"/api/internships/applications/{app.sqid}/accept", **headers)
        app.refresh_from_db()
        self.assertIsNotNone(app.responded_at)

    def test_cannot_accept_already_accepted(self):
        app = self._create_application()
        app.accept()
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(f"/api/internships/applications/{app.sqid}/accept", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_accept_rejected(self):
        app = self._create_application()
        app.reject()
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(f"/api/internships/applications/{app.sqid}/accept", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_cannot_accept(self):
        app = self._create_application()
        headers = self._auth_header(self.student)
        resp = self.client.post(f"/api/internships/applications/{app.sqid}/accept", **headers)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_alumnus_cannot_accept(self):
        app = self._create_application()
        headers = self._auth_header(self.other_alumnus)
        resp = self.client.post(f"/api/internships/applications/{app.sqid}/accept", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # --- REJECT ---
    def test_reject_returns_200(self):
        app = self._create_application()
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(f"/api/internships/applications/{app.sqid}/reject", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(app.status, EngagementLifecycleStatus.REJECTED)

    def test_cannot_reject_rejected(self):
        app = self._create_application()
        app.reject()
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(f"/api/internships/applications/{app.sqid}/reject", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # --- WITHDRAW ---
    def test_withdraw_returns_200(self):
        app = self._create_application()
        headers = self._auth_header(self.student)
        resp = self.client.post(f"/api/internships/applications/{app.sqid}/withdraw", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(app.status, EngagementLifecycleStatus.WITHDRAWN)

    def test_cannot_withdraw_withdrawn(self):
        app = self._create_application()
        app.withdraw()
        headers = self._auth_header(self.student)
        resp = self.client.post(f"/api/internships/applications/{app.sqid}/withdraw", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_student_cannot_withdraw(self):
        app = self._create_application()
        headers = self._auth_header(self.other_student)
        resp = self.client.post(f"/api/internships/applications/{app.sqid}/withdraw", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
