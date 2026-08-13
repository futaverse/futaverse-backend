from engagements.models import Engagement
from engagements.services import (
    create_engagement,
    engagement_domain,
    feed_event_type,
    get_engagement_detail,
    get_engagement_post_context,
    default_share_text,
    default_completion_text,
)
from futaverse.tests_helpers import BaseAPITestCase
from internships.models import InternshipApplication, InternshipOffer


class EngagementServiceTests(BaseAPITestCase):
    def setUp(self):
        self.student = self._create_student("stu@test.com")
        self.alumnus = self._create_alumnus("alum@test.com")
        self.internship = self.make_internship(alumnus_user=self.alumnus)

    def _make(self):
        return self.make_engagement(
            Engagement.EngagementType.INTERNSHIP,
            student_user=self.student,
            alumnus_user=self.alumnus,
            internship=self.internship,
        )

    def test_create_engagement_creates_shared_and_detail_rows(self):
        engagement = self._make()
        self.assertEqual(engagement.engagement_type, Engagement.EngagementType.INTERNSHIP)
        detail = get_engagement_detail(engagement)
        self.assertIsNotNone(detail)
        self.assertEqual(detail.internship, self.internship)
        self.assertEqual(detail.engagement_id, engagement.id)

    def test_get_engagement_detail_returns_none_without_detail_row(self):
        engagement = Engagement.objects.create(
            engagement_type=Engagement.EngagementType.INTERNSHIP,
            student=self.student.student_profile,
            alumnus=self.alumnus.alumni_profile,
        )
        self.assertIsNone(get_engagement_detail(engagement))

    def test_post_context_internship(self):
        context = get_engagement_post_context(self._make())
        self.assertEqual(context["type"], "internship")
        self.assertEqual(context["company"], self.internship.company)
        self.assertEqual(context["title"], self.internship.title)

    def test_default_share_text_internship(self):
        text = default_share_text(self._make())
        self.assertIn(self.internship.company, text)
        self.assertIn(self.internship.title, text)

    def test_default_completion_text_internship(self):
        text = default_completion_text(self._make())
        self.assertIn("completed", text)
        self.assertIn(self.internship.company, text)

    def test_feed_event_type_internship(self):
        from feed.models import FeedEvent
        self.assertEqual(feed_event_type(self._make()), FeedEvent.EventType.INTERNSHIP_STARTED)

    def test_domain(self):
        self.assertEqual(engagement_domain(self._make()), "internship")

    def test_create_engagement_rejects_both_origins(self):
        app = self.make_application(
            InternshipApplication, student_user=self.student, internship=self.internship
        )
        offer = self.make_offer(
            InternshipOffer, student_user=self.student, internship=self.internship
        )
        with self.assertRaises(ValueError):
            create_engagement(
                engagement_type=Engagement.EngagementType.INTERNSHIP,
                student=self.student.student_profile,
                alumnus=self.alumnus.alumni_profile,
                application=app,
                offer=offer,
            )
