from django.test import TestCase
from django.urls import path

from core.models import User, AlumniProfile
from internships.models import Internship
from engagements.helpers import queryset_by_role, generate_engagement_urls


class QuerysetByRoleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alumnus_user = User.objects.create_user(
            email="alum@test.com", password="p", role=User.Role.ALUMNI, is_active=True
        )
        cls.alumnus_profile = AlumniProfile.objects.create(
            user=cls.alumnus_user, phone_num="0801", gender="male",
            firstname="A", lastname="B", address="X", state="Lagos",
            country="NG", department="CS", faculty="Eng", grad_year="2020",
            current_job_title="SE", current_company="TC", industry="Tech", years_of_exp=3,
        )
        cls.other_alumnus_user = User.objects.create_user(
            email="other@test.com", password="p", role=User.Role.ALUMNI, is_active=True
        )
        cls.other_alumnus_profile = AlumniProfile.objects.create(
            user=cls.other_alumnus_user, phone_num="0802", gender="male",
            firstname="C", lastname="D", address="Y", state="Ogun",
            country="NG", department="CS", faculty="Eng", grad_year="2020",
            current_job_title="Dev", current_company="OC", industry="Tech", years_of_exp=2,
        )
        cls.student_user = User.objects.create_user(
            email="stu@test.com", password="p", role=User.Role.STUDENT, is_active=True
        )
        cls.internship1 = Internship.objects.create(
            alumnus=cls.alumnus_profile, title="Intern1", description="d",
            work_mode="Remote", engagement_type="Full-time", location="Remote",
            skills_required=[], duration_weeks=12,
            start_date="2026-01-01", end_date="2026-03-31",
            is_paid=True, stipend=100000, levels=[300],
            company="TC", company_type="Tech", industry="Tech",
            available_slots=5, remaining_slots=5,
        )
        cls.internship2 = Internship.objects.create(
            alumnus=cls.other_alumnus_profile, title="Intern2", description="d",
            work_mode="Remote", engagement_type="Full-time", location="Remote",
            skills_required=[], duration_weeks=12,
            start_date="2026-01-01", end_date="2026-03-31",
            is_paid=True, stipend=100000, levels=[300],
            company="OC", company_type="Tech", industry="Tech",
            available_slots=5, remaining_slots=5,
        )

    def test_alumnus_filters_by_their_profile(self):
        qs = queryset_by_role(
            self.alumnus_user, Internship,
            alumnus_filter={"alumnus": self.alumnus_user.alumni_profile},
            student_filter={},
        )
        results = list(qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Intern1")

    def test_student_gets_empty_when_no_filter_matches(self):
        qs = queryset_by_role(
            self.student_user, Internship,
            alumnus_filter={},
            student_filter={"alumnus": None},
        )
        self.assertEqual(list(qs), [])

    def test_unknown_role_returns_empty(self):
        no_role_user = User.objects.create_user(
            email="norole@test.com", password="p", role=User.Role.ADMIN, is_active=True
        )
        qs = queryset_by_role(
            no_role_user, Internship,
            alumnus_filter={}, student_filter={},
        )
        self.assertEqual(list(qs), [])

    def test_select_related_is_applied(self):
        qs = queryset_by_role(
            self.alumnus_user, Internship,
            alumnus_filter={"alumnus": self.alumnus_user.alumni_profile},
            student_filter={},
            select_related=("alumnus",),
        )
        result = qs.first()
        self.assertEqual(result.alumnus.id, self.alumnus_profile.id)

    def test_order_by_is_applied(self):
        qs = queryset_by_role(
            self.alumnus_user, Internship,
            alumnus_filter={"alumnus": self.alumnus_user.alumni_profile},
            student_filter={},
            order_by="-created_at",
        )
        results = list(qs)
        self.assertEqual(len(results), 1)


class GenerateEngagementUrlsTests(TestCase):
    def test_returns_url_patterns_with_expected_count(self):
        patterns = generate_engagement_urls(
            prefix="test",
            entity_views={
                "list_create": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "rud": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "toggle_active": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
            },
            application_views={
                "create": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "list": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "retrieve": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "accept": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "reject": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "withdraw": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
            },
            offer_views={
                "create": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "list": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "retrieve": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "accept": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "reject": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "withdraw": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
            },
            engagement_views={
                "list": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "retrieve": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "completed": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "acknowledged": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
            },
        )
        self.assertIsInstance(patterns, list)
        self.assertGreater(len(patterns), 15)
        self.assertEqual(patterns[0].name, "create-test-application")

    def test_extra_paths_are_appended(self):
        extra = [path("/custom-endpoint", lambda r: None, name="custom")]
        patterns = generate_engagement_urls(
            prefix="test",
            entity_views={
                "list_create": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "rud": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "toggle_active": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
            },
            application_views={
                "create": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "list": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "retrieve": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "accept": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "reject": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "withdraw": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
            },
            offer_views={
                "create": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "list": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "retrieve": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "accept": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "reject": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "withdraw": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
            },
            engagement_views={
                "list": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "retrieve": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "completed": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
                "acknowledged": type("V", (), {"as_view": classmethod(lambda cls: lambda r: None)}),
            },
            extra=extra,
        )
        names = [p.name for p in patterns]
        self.assertIn("custom", names)
