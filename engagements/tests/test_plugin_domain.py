from django.test import TestCase

from engagements.plugins import (
    get_engagement_plugin,
    _internship_engagement_plugin,
    _mentorship_engagement_plugin,
)


class PluginDomainFieldTests(TestCase):
    """Locks in Task 2 fix: plugin must expose 'domain' field."""

    def test_internship_plugin_has_domain_field(self):
        self.assertEqual(_internship_engagement_plugin["domain"], "internship")

    def test_mentorship_plugin_has_domain_field(self):
        self.assertEqual(_mentorship_engagement_plugin["domain"], "mentorship")

    def test_get_plugin_by_string_key_returns_correct_domain(self):
        plugin = get_engagement_plugin("internship_engagement")
        self.assertEqual(plugin["domain"], "internship")

    def test_get_plugin_by_mentorship_string_key(self):
        plugin = get_engagement_plugin("mentorship_engagement")
        self.assertEqual(plugin["domain"], "mentorship")

    def test_get_plugin_for_unknown_type_returns_none(self):
        self.assertIsNone(get_engagement_plugin("nonexistent_type"))
