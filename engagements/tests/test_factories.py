from engagements.models import Engagement
from futaverse.tests_helpers import BaseAPITestCase


class EngagementFactoryTests(BaseAPITestCase):
    def test_make_internship_factory_works(self):
        alumnus = self._create_alumnus("alum@test.com")
        internship = self.make_internship(alumnus_user=alumnus)
        self.assertIsNotNone(internship.sqid)
        self.assertEqual(internship.remaining_slots, internship.available_slots)

    def test_make_engagement_factory_works(self):
        alumnus = self._create_alumnus("alum@test.com")
        student = self._create_student("stu@test.com")
        internship = self.make_internship(alumnus_user=alumnus)
        engagement = self.make_engagement(
            Engagement.EngagementType.INTERNSHIP,
            student_user=student,
            alumnus_user=alumnus,
            internship=internship,
        )
        self.assertIsNotNone(engagement.sqid)
        self.assertEqual(engagement.status, Engagement.EngagementStatus.ACTIVE)
        self.assertEqual(engagement.engagement_type, Engagement.EngagementType.INTERNSHIP)

    def test_make_application_factory_works(self):
        alumnus = self._create_alumnus("alum@test.com")
        student = self._create_student("stu@test.com")
        internship = self.make_internship(alumnus_user=alumnus)
        from engagements.models import EngagementLifecycleStatus
        from internships.models import InternshipApplication
        app = self.make_application(
            InternshipApplication,
            student_user=student,
            internship=internship,
        )
        self.assertEqual(app.status, EngagementLifecycleStatus.PENDING)
