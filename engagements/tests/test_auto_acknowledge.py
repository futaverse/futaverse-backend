from unittest.mock import patch

from django.test import TestCase

from engagements.tasks import auto_acknowledge_engagement
from engagements.models import Engagement
from futaverse.tests_helpers import BaseAPITestCase


class AutoAcknowledgeEngagementTests(BaseAPITestCase):
    """Locks in Task 2 fix and the None-safety fallback."""

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

    @patch("engagements.tasks.async_task")
    def test_completed_engagement_is_acknowledged(self, mock_task):
        self.engagement.status = Engagement.EngagementStatus.COMPLETED
        self.engagement.save(update_fields=["status"])

        auto_acknowledge_engagement(self.engagement.sqid, "internship_engagement")

        self.engagement.refresh_from_db()
        self.assertEqual(self.engagement.status, Engagement.EngagementStatus.ACKNOWLEDGED)

    @patch("engagements.tasks.async_task")
    def test_active_engagement_is_not_acknowledged(self, mock_task):
        self.engagement.status = Engagement.EngagementStatus.ACTIVE
        self.engagement.save(update_fields=["status"])

        auto_acknowledge_engagement(self.engagement.sqid, "internship_engagement")

        self.engagement.refresh_from_db()
        self.assertEqual(self.engagement.status, Engagement.EngagementStatus.ACTIVE)
        mock_task.assert_not_called()

    @patch("engagements.tasks.async_task")
    def test_notification_uses_plugin_domain_not_string_replace(self, mock_task):
        """Task 2 fix: notification content must use plugin['domain'], not replace()."""
        self.engagement.status = Engagement.EngagementStatus.COMPLETED
        self.engagement.save(update_fields=["status"])

        auto_acknowledge_engagement(self.engagement.sqid, "internship_engagement")

        mock_task.assert_called_once()
        content = mock_task.call_args.kwargs["content"]
        self.assertIn("Your internship with", content)
        self.assertNotIn("internship_engagement with", content)

    @patch("engagements.tasks.async_task")
    def test_unknown_engagement_type_raises_value_error(self, mock_task):
        """Locks in: unknown engagement_type raises ValueError, not AttributeError."""
        with self.assertRaises(ValueError):
            auto_acknowledge_engagement("fakesqid123", "nonexistent_type")
