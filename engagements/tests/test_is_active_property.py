from engagements.models import Engagement
from futaverse.tests_helpers import BaseAPITestCase


class IsStatusActivePropertyTests(BaseAPITestCase):
    """Locks in Task 16 fix: is_status_active is the new name."""

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

    def test_active_engagement_is_status_active(self):
        self.engagement.status = Engagement.EngagementStatus.ACTIVE
        self.engagement.save(update_fields=["status"])
        self.engagement.refresh_from_db()
        self.assertTrue(self.engagement.is_status_active)

    def test_completed_engagement_is_not_status_active(self):
        self.engagement.status = Engagement.EngagementStatus.COMPLETED
        self.engagement.save(update_fields=["status"])
        self.engagement.refresh_from_db()
        self.assertFalse(self.engagement.is_status_active)

    def test_old_is_active_property_does_not_exist(self):
        """Anti-regression: the old `is_active` property must NOT exist on engagement."""
        self.assertFalse(hasattr(Engagement, "is_active") and isinstance(Engagement.is_active, property))
