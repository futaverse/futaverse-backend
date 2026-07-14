from django.test import TestCase
from unittest.mock import patch

from posts.services import share_engagement, share_engagement_completion
from futaverse.tests_helpers import BaseAPITestCase
from internships.models import InternshipEngagement


class ShareEngagementImportTests(TestCase):
    """Locks in B1: share_engagement_completion must be importable."""

    def test_share_engagement_completion_is_importable(self):
        self.assertTrue(callable(share_engagement_completion))

    def test_share_engagement_is_importable(self):
        self.assertTrue(callable(share_engagement))


class ShareEngagementBehaviorTests(BaseAPITestCase):
    """Locks in B3: plugin dict must have 'model' key (not 'model_key')."""

    def setUp(self):
        self.student = self._create_student("stu@test.com")
        self.alumnus = self._create_alumnus("alum@test.com")
        self.internship = self.make_internship(alumnus_user=self.alumnus)
        self.engagement = self.make_engagement(
            InternshipEngagement,
            student_user=self.student,
            alumnus_user=self.alumnus,
            internship=self.internship,
        )

    @patch("posts.services.async_task")
    def test_share_engagement_passes_correct_model_key_to_feed(self, mock_task):
        """B3: The 'model' key (not 'model_key') must reach create_feed_event_task."""
        share_engagement(user=self.student, engagement=self.engagement)

        self.assertTrue(mock_task.called)
        call_kwargs = mock_task.call_args.kwargs
        self.assertEqual(call_kwargs["related_model"], "internship_engagement")

    @patch("posts.services.async_task")
    def test_share_engagement_completion_passes_correct_model_key(self, mock_task):
        """B3: same fix must apply to share_engagement_completion."""
        share_engagement_completion(user=self.student, engagement=self.engagement)

        self.assertTrue(mock_task.called)
        call_kwargs = mock_task.call_args.kwargs
        self.assertEqual(call_kwargs["related_model"], "internship_engagement")
