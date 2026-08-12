from rest_framework import status

from internships.models import Internship, InternshipApplication, InternshipEngagement
from engagements.models import EngagementLifecycleStatus
from core.models import StudentResume
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

    def _create_resume(self, student_user, filename="resume.pdf"):
        return StudentResume.objects.create(
            student=student_user.student_profile,
            resume=f"http://example.com/resumes/{filename}",
            filename=filename,
        )

    def _create_internship(self, **kwargs):
        defaults = {
            "alumnus": self.alumnus.alumni_profile,
            "title": "SE Intern", "description": "desc", "work_mode": "Remote",
            "engagement_type": "Full-time", "location": "Lagos", "duration_weeks": 12,
            "start_date": "2026-01-01", "end_date": "2026-03-31",
            "is_paid": True, "stipend": 100000, "levels": [300],
            "company": "TC", "company_type": "Tech", "industry": "Tech",
            "available_slots": 5, "remaining_slots": 5,
            "require_resume": False,
        }
        defaults.update(kwargs)
        return Internship.objects.create(**defaults)

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

    # --- RESUME ---
    def test_apply_with_own_resume_returns_201(self):
        resume = self._create_resume(self.student)
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/internships/application", {
            "internship": self.internship.sqid,
            "resume": resume.sqid,
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["resume_info"]["sqid"], resume.sqid)
        self.assertEqual(resp.data["resume_info"]["resume"], resume.resume)

    def test_apply_with_other_students_resume_returns_400(self):
        resume = self._create_resume(self.other_student)
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/internships/application", {
            "internship": self.internship.sqid,
            "resume": resume.sqid,
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_apply_with_soft_deleted_resume_returns_400(self):
        resume = self._create_resume(self.student)
        resume.soft_delete()
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/internships/application", {
            "internship": self.internship.sqid,
            "resume": resume.sqid,
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_apply_without_resume_when_required_returns_400(self):
        internship = self._create_internship(require_resume=True)
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/internships/application", {
            "internship": internship.sqid,
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_apply_with_resume_when_required_returns_201(self):
        internship = self._create_internship(require_resume=True)
        resume = self._create_resume(self.student)
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/internships/application", {
            "internship": internship.sqid,
            "resume": resume.sqid,
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["resume_info"]["sqid"], resume.sqid)

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

    def test_alumnus_sees_resume_info_on_application(self):
        resume = self._create_resume(self.student)
        app = self._create_application()
        app.resume = resume
        app.save(update_fields=["resume"])
        headers = self._auth_header(self.alumnus)
        resp = self.client.get("/api/internships/applications", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        application = resp.data[0]
        self.assertEqual(application["resume_info"]["sqid"], resume.sqid)
        self.assertEqual(application["resume_info"]["resume"], resume.resume)

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
