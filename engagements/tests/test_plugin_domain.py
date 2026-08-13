from django.test import TestCase

from engagements.models import Engagement
from engagements.plugins import ENGAGEMENT_PLUGIN, get_engagement_plugin
from engagements.services import engagement_domain


class PluginRegistryTests(TestCase):
    """Locks in the single-string-keyed registry and service domain resolution."""

    def test_registry_is_keyed_by_engagement_type_only(self):
        self.assertEqual(
            set(ENGAGEMENT_PLUGIN.keys()),
            set(Engagement.EngagementType.values),
        )

    def test_internship_plugin_has_serializer(self):
        self.assertTrue(ENGAGEMENT_PLUGIN[Engagement.EngagementType.INTERNSHIP]["serializer"])

    def test_get_plugin_by_string_key(self):
        self.assertIsNotNone(get_engagement_plugin("internship_engagement"))
        self.assertIsNotNone(get_engagement_plugin("mentorship_engagement"))

    def test_get_plugin_for_unknown_type_returns_none(self):
        self.assertIsNone(get_engagement_plugin("nonexistent_type"))

    def test_domain_resolution(self):
        engagement = Engagement(engagement_type=Engagement.EngagementType.INTERNSHIP)
        self.assertEqual(engagement_domain(engagement), "internship")
