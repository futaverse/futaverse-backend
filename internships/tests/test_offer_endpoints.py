from rest_framework import status

from internships.models import Internship, InternshipOffer, InternshipEngagement
from engagements.models import EngagementLifecycleStatus
from futaverse.tests_helpers import BaseAPITestCase


class InternshipOfferEndpointTests(BaseAPITestCase):
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

    def _create_offer(self, student=None, internship=None):
        return InternshipOffer.objects.create(
            internship=internship or self.internship,
            student=(student or self.student).student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )

    # --- CREATE ---
    def test_alumnus_can_create_offer(self):
        headers = self._auth_header(self.alumnus)
        resp = self.client.post("/api/internships/offer", {
            "internship": self.internship.sqid,
            "student": self.student.student_profile.sqid,
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("sqid", resp.data)

    def test_cannot_create_duplicate_offer(self):
        self._create_offer()
        headers = self._auth_header(self.alumnus)
        resp = self.client.post("/api/internships/offer", {
            "internship": self.internship.sqid,
            "student": self.student.student_profile.sqid,
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_create_offer_for_inactive_internship(self):
        self.internship.is_active = False
        self.internship.save(update_fields=["is_active"])
        headers = self._auth_header(self.alumnus)
        resp = self.client.post("/api/internships/offer", {
            "internship": self.internship.sqid,
            "student": self.student.student_profile.sqid,
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_create_offer_for_already_engaged_student(self):
        InternshipEngagement.objects.create(
            internship=self.internship, student=self.student.student_profile,
            alumnus=self.alumnus.alumni_profile, source="offer", source_id=1,
        )
        headers = self._auth_header(self.alumnus)
        resp = self.client.post("/api/internships/offer", {
            "internship": self.internship.sqid,
            "student": self.student.student_profile.sqid,
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_cannot_create_offer(self):
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/internships/offer", {
            "internship": self.internship.sqid,
            "student": self.student.student_profile.sqid,
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_alumnus_cannot_create_offer(self):
        headers = self._auth_header(self.other_alumnus)
        resp = self.client.post("/api/internships/offer", {
            "internship": self.internship.sqid,
            "student": self.student.student_profile.sqid,
        }, **headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_create_offer(self):
        resp = self.client.post("/api/internships/offer", {
            "internship": self.internship.sqid,
            "student": self.student.student_profile.sqid,
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- LIST ---
    def test_alumnus_lists_own_offers(self):
        self._create_offer()
        headers = self._auth_header(self.alumnus)
        resp = self.client.get("/api/internships/offers", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_student_sees_own_offers(self):
        self._create_offer()
        headers = self._auth_header(self.student)
        resp = self.client.get("/api/internships/offers", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_student_does_not_see_others_offers(self):
        self._create_offer()
        headers = self._auth_header(self.other_student)
        resp = self.client.get("/api/internships/offers", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)

    # --- RETRIEVE ---
    def test_student_retrieves_own_offer(self):
        offer = self._create_offer()
        headers = self._auth_header(self.student)
        resp = self.client.get(f"/api/internships/offers/{offer.sqid}", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["sqid"], offer.sqid)

    def test_other_student_gets_404_on_offer(self):
        offer = self._create_offer()
        headers = self._auth_header(self.other_student)
        resp = self.client.get(f"/api/internships/offers/{offer.sqid}", **headers)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # --- ACCEPT ---
    def test_student_accepts_offer_returns_201_with_engagement(self):
        offer = self._create_offer()
        headers = self._auth_header(self.student)
        resp = self.client.post(f"/api/internships/offers/{offer.sqid}/accept", **headers)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("engagement", resp.data)
        self.assertIn("sqid", resp.data["engagement"])

    def test_accept_offer_decrements_remaining(self):
        offer = self._create_offer()
        before = self.internship.remaining_slots
        headers = self._auth_header(self.student)
        self.client.post(f"/api/internships/offers/{offer.sqid}/accept", **headers)
        self.internship.refresh_from_db()
        self.assertEqual(self.internship.remaining_slots, before - 1)

    def test_accept_offer_sets_offer_status_accepted(self):
        offer = self._create_offer()
        headers = self._auth_header(self.student)
        self.client.post(f"/api/internships/offers/{offer.sqid}/accept", **headers)
        offer.refresh_from_db()
        self.assertEqual(offer.status, EngagementLifecycleStatus.ACCEPTED)
        self.assertIsNotNone(offer.responded_at)

    def test_cannot_accept_non_pending_offer(self):
        offer = self._create_offer()
        offer.accept()
        headers = self._auth_header(self.student)
        resp = self.client.post(f"/api/internships/offers/{offer.sqid}/accept", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_accept_rejected_offer(self):
        offer = self._create_offer()
        offer.reject()
        headers = self._auth_header(self.student)
        resp = self.client.post(f"/api/internships/offers/{offer.sqid}/accept", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_student_cannot_accept_offer(self):
        offer = self._create_offer()
        headers = self._auth_header(self.other_student)
        resp = self.client.post(f"/api/internships/offers/{offer.sqid}/accept", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_already_engaged_student_cannot_accept(self):
        InternshipEngagement.objects.create(
            internship=self.internship, student=self.student.student_profile,
            alumnus=self.alumnus.alumni_profile, source="offer", source_id=1,
        )
        offer = self._create_offer()
        headers = self._auth_header(self.student)
        resp = self.client.post(f"/api/internships/offers/{offer.sqid}/accept", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # --- REJECT ---
    def test_student_rejects_offer(self):
        offer = self._create_offer()
        headers = self._auth_header(self.student)
        resp = self.client.post(f"/api/internships/offers/{offer.sqid}/reject", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        offer.refresh_from_db()
        self.assertEqual(offer.status, EngagementLifecycleStatus.REJECTED)

    def test_cannot_reject_rejected_offer(self):
        offer = self._create_offer()
        offer.reject()
        headers = self._auth_header(self.student)
        resp = self.client.post(f"/api/internships/offers/{offer.sqid}/reject", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_student_cannot_reject_offer(self):
        offer = self._create_offer()
        headers = self._auth_header(self.other_student)
        resp = self.client.post(f"/api/internships/offers/{offer.sqid}/reject", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # --- WITHDRAW ---
    def test_alumnus_withdraws_offer(self):
        offer = self._create_offer()
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(f"/api/internships/offers/{offer.sqid}/withdraw", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        offer.refresh_from_db()
        self.assertEqual(offer.status, EngagementLifecycleStatus.WITHDRAWN)

    def test_cannot_withdraw_withdrawn_offer(self):
        offer = self._create_offer()
        offer.withdraw()
        headers = self._auth_header(self.alumnus)
        resp = self.client.post(f"/api/internships/offers/{offer.sqid}/withdraw", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_alumnus_cannot_withdraw_offer(self):
        offer = self._create_offer()
        headers = self._auth_header(self.other_alumnus)
        resp = self.client.post(f"/api/internships/offers/{offer.sqid}/withdraw", **headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_cannot_withdraw_offer(self):
        offer = self._create_offer()
        headers = self._auth_header(self.student)
        resp = self.client.post(f"/api/internships/offers/{offer.sqid}/withdraw", **headers)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # --- Response shape checks ---
    def test_offer_response_has_internship_info(self):
        offer = self._create_offer()
        headers = self._auth_header(self.student)
        resp = self.client.get(f"/api/internships/offers/{offer.sqid}", **headers)
        self.assertIn("internship_info", resp.data)

    def test_offer_response_has_student_info(self):
        offer = self._create_offer()
        headers = self._auth_header(self.student)
        resp = self.client.get(f"/api/internships/offers/{offer.sqid}", **headers)
        self.assertIn("student_info", resp.data)

    def test_offer_response_has_alumnus_info(self):
        offer = self._create_offer()
        headers = self._auth_header(self.student)
        resp = self.client.get(f"/api/internships/offers/{offer.sqid}", **headers)
        self.assertIn("alumnus_info", resp.data)
