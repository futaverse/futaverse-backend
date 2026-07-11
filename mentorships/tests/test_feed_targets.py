from django.test import TestCase

from mentorships.models import Mentorship
from mentorships.lib import MentorshipCategory
from core.models import User, AlumniProfile


class MentorshipFeedTargetsTests(TestCase):
    """B8: Mentorship.feed_targets must return proper targets."""

    def setUp(self):
        user = User.objects.create_user(
            email="alumnus@test.com", password="pass", role=User.Role.ALUMNI, is_active=True
        )
        self.alumnus = AlumniProfile.objects.create(
            user=user, phone_num="08000000000", gender="male",
            firstname="A", lastname="B",
            address="Addr", state="LA", country="NG",
            department="CS", faculty="Eng", grad_year="2020",
            current_job_title="SE", current_company="TC", industry="Tech", years_of_exp=5,
        )
        self.mentorship = Mentorship.objects.create(
            alumnus=self.alumnus,
            title="Test Mentorship",
            description="Desc",
            category=MentorshipCategory.TECHNICAL,
            focus_areas=["software_engineering", "data_science"],
            work_mode="Remote",
            is_active=True,
        )

    def test_feed_targets_includes_focus_areas_as_skills(self):
        targets = self.mentorship.feed_targets
        skill_targets = [t for t in targets if t["target_type"] == "skill"]
        self.assertEqual(len(skill_targets), 2)

    def test_feed_targets_includes_category(self):
        targets = self.mentorship.feed_targets
        category_target = next((t for t in targets if t["target_type"] == "category"), None)
        self.assertIsNotNone(category_target)
