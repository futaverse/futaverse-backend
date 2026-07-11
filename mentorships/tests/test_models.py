from django.test import TestCase

from mentorships.models import Mentorship
from mentorships.lib import MentorshipCategory


class MentorshipModelTests(TestCase):
    def test_category_uses_mentorship_category_choices(self):
        """B4: Mentorship.category must use MentorshipCategory.choices, not FocusArea.choices."""
        field = Mentorship._meta.get_field("category")
        expected_choices = {c[0] for c in MentorshipCategory.choices}
        actual_choices = {c[0] for c in field.choices}
        self.assertEqual(
            actual_choices,
            expected_choices,
            "Mentorship.category choices should match MentorshipCategory",
        )
