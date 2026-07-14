from unittest.mock import patch

from django.test import TestCase

from engagements.tasks import schedule_auto_acknowledgement_task


class ScheduleAutoAcknowledgeSafetyTests(TestCase):
    """Locks in Task 13 fix: None plugin must not crash."""

    @patch("engagements.tasks.async_task")
    @patch("engagements.tasks.schedule")
    def test_unknown_engagement_type_raises_value_error(self, mock_schedule, mock_async_task):
        with self.assertRaises(ValueError):
            schedule_auto_acknowledgement_task({
                "engagement_type": "nonexistent_type",
                "sqid": "fakesqid",
            })
        mock_async_task.assert_not_called()
        mock_schedule.assert_not_called()

    @patch("engagements.tasks.async_task")
    @patch("engagements.tasks.schedule")
    def test_nonexistent_engagement_does_not_crash(self, mock_schedule, mock_async_task):
        """A valid type with a non-existent sqid should return cleanly."""
        schedule_auto_acknowledgement_task({
            "engagement_type": "internship_engagement",
            "sqid": "fakesqid",
        })
        mock_async_task.assert_not_called()
        mock_schedule.assert_not_called()
