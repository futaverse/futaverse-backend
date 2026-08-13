from rest_framework import status

from engagements.models import Engagement
from futaverse.tests_helpers import BaseAPITestCase


class CreateReviewEngagementResolutionTests(BaseAPITestCase):
    def setUp(self):
        self.student = self._create_student("stu@test.com")
        self.alumnus = self._create_alumnus("alum@test.com")
        self.internship = self.make_internship(alumnus_user=self.alumnus)
        self.engagement = self.make_engagement(
            Engagement.EngagementType.INTERNSHIP,
            student_user=self.student,
            alumnus_user=self.alumnus,
            internship=self.internship,
        )
        self.engagement.status = Engagement.EngagementStatus.ACKNOWLEDGED
        self.engagement.save(update_fields=["status"])

    def _payload(self, **overrides):
        payload = {
            "engagement_type": "internship_engagement",
            "engagement": self.engagement.sqid,
            "review_text": "Great mentor!",
            "metrics": {
                "communication": 5, "availability": 4, "guidance_quality": 5,
                "industry_knowledge": 4, "supportiveness": 5,
            },
        }
        payload.update(overrides)
        return payload

    def test_student_can_review_acknowledged_engagement(self):
        resp = self.client.post(
            "/api/reviews",
            self._payload(),
            **self._auth_header(self.student),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_type_mismatch_returns_404(self):
        resp = self.client.post(
            "/api/reviews",
            self._payload(engagement_type="mentorship_engagement"),
            **self._auth_header(self.student),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unacknowledged_engagement_is_rejected(self):
        self.engagement.status = Engagement.EngagementStatus.ACTIVE
        self.engagement.save(update_fields=["status"])
        resp = self.client.post(
            "/api/reviews",
            self._payload(),
            **self._auth_header(self.student),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
