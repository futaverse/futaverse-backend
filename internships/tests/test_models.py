from django.db import models
from django.test import TestCase

from internships.models import Internship, InternshipApplication
from futaverse.tests_helpers import BaseAPITestCase


class InternshipModelTests(BaseAPITestCase):
    def test_company_has_max_length(self):
        """B5: company CharField must define max_length."""
        field = Internship._meta.get_field("company")
        self.assertIsNotNone(field.max_length)

    def test_company_type_has_max_length(self):
        """B5: company_type CharField must define max_length."""
        field = Internship._meta.get_field("company_type")
        self.assertIsNotNone(field.max_length)

    def test_application_responded_at_not_auto_now(self):
        """B7: responded_at must NOT have auto_now (only set on status change)."""
        field = InternshipApplication._meta.get_field("responded_at")
        self.assertFalse(field.auto_now)

    def test_application_responded_at_nullable(self):
        """B7: responded_at must be nullable (starts null, set on first transition)."""
        field = InternshipApplication._meta.get_field("responded_at")
        self.assertTrue(field.null)

    def test_application_resume_nullable(self):
        """Applications may be created without a resume."""
        field = InternshipApplication._meta.get_field("resume")
        self.assertTrue(field.null)

    def test_application_resume_protected(self):
        """A resume referenced by an application can never be hard-deleted."""
        field = InternshipApplication._meta.get_field("resume")
        self.assertEqual(field.remote_field.on_delete, models.PROTECT)
