from django.test import TestCase

from core.models import User, StudentProfile, AlumniProfile
from engagements.models import Engagement


class EngagementModelTests(TestCase):
    def test_engagement_type_choices_match_public_api_strings(self):
        self.assertEqual(Engagement.EngagementType.INTERNSHIP, "internship_engagement")
        self.assertEqual(Engagement.EngagementType.MENTORSHIP, "mentorship_engagement")

    def test_default_status_is_active_and_sqid_assigned(self):
        student_user = User.objects.create_user(email="s@t.com", password="p", role=User.Role.STUDENT, is_active=True)
        student = StudentProfile.objects.create(
            user=student_user, phone_num="0801", gender="male", firstname="S", lastname="T",
            address="X", state="Lagos", country="NG", department="CS", faculty="Eng",
            level=300, cgpa=4.0, skills=[], expected_grad_year="2027",
        )
        alumnus_user = User.objects.create_user(email="a@t.com", password="p", role=User.Role.ALUMNI, is_active=True)
        alumnus = AlumniProfile.objects.create(
            user=alumnus_user, phone_num="0802", gender="male", firstname="A", lastname="B",
            address="Y", state="Ogun", country="NG", department="CS", faculty="Eng",
            grad_year="2020", current_job_title="SE", current_company="TC",
            industry="Tech", years_of_exp=3,
        )
        engagement = Engagement.objects.create(
            engagement_type=Engagement.EngagementType.INTERNSHIP,
            student=student,
            alumnus=alumnus,
        )
        self.assertEqual(engagement.status, Engagement.EngagementStatus.ACTIVE)
        self.assertTrue(engagement.is_status_active)
        self.assertIsNotNone(engagement.sqid)

    def test_update_status_persists_via_update_fields(self):
        student_user = User.objects.create_user(email="s2@t.com", password="p", role=User.Role.STUDENT, is_active=True)
        student = StudentProfile.objects.create(
            user=student_user, phone_num="0801", gender="male", firstname="S", lastname="T",
            address="X", state="Lagos", country="NG", department="CS", faculty="Eng",
            level=300, cgpa=4.0, skills=[], expected_grad_year="2027",
        )
        alumnus_user = User.objects.create_user(email="a2@t.com", password="p", role=User.Role.ALUMNI, is_active=True)
        alumnus = AlumniProfile.objects.create(
            user=alumnus_user, phone_num="0802", gender="male", firstname="A", lastname="B",
            address="Y", state="Ogun", country="NG", department="CS", faculty="Eng",
            grad_year="2020", current_job_title="SE", current_company="TC",
            industry="Tech", years_of_exp=3,
        )
        engagement = Engagement.objects.create(
            engagement_type=Engagement.EngagementType.MENTORSHIP,
            student=student,
            alumnus=alumnus,
        )
        engagement.update_status(Engagement.EngagementStatus.COMPLETED)
        engagement.refresh_from_db()
        self.assertEqual(engagement.status, Engagement.EngagementStatus.COMPLETED)
        self.assertFalse(engagement.is_status_active)
