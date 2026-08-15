from django.test import TestCase
from django.test.client import RequestFactory

from core.models import User, StudentProfile, AlumniProfile
from internships.models import Internship, InternshipApplication, InternshipOffer
from engagements.models import Engagement
from engagements.services import create_engagement

from engagements.serializers import (
    make_student_manage_offer_serializer,
    make_alumnus_manage_offer_serializer,
    make_student_manage_application_serializer,
    make_alumnus_manage_application_serializer,
)


class StudentManageOfferSerializerFactoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.alumnus_user = User.objects.create_user(
            email="alum@test.com", password="p", role=User.Role.ALUMNI, is_active=True
        )
        cls.alumnus_profile = AlumniProfile.objects.create(
            user=cls.alumnus_user, phone_num="0801", gender="male",
            firstname="A", lastname="B", address="X", state="Lagos",
            country="NG", department="CS", faculty="Eng", grad_year="2020",
            current_job_title="SE", current_company="TC", industry="Tech", years_of_exp=3,
        )
        cls.student_user = User.objects.create_user(
            email="stu@test.com", password="p", role=User.Role.STUDENT, is_active=True
        )
        cls.student_profile = StudentProfile.objects.create(
            user=cls.student_user, phone_num="0802", gender="male",
            firstname="C", lastname="D", address="Y", state="Lagos",
            country="NG", department="CS", faculty="Eng",
            level=300, cgpa=4.0, skills=[], expected_grad_year="2027",
        )
        cls.wrong_student_user = User.objects.create_user(
            email="wrong@test.com", password="p", role=User.Role.STUDENT, is_active=True
        )
        cls.wrong_student_profile = StudentProfile.objects.create(
            user=cls.wrong_student_user, phone_num="0803", gender="male",
            firstname="E", lastname="F", address="Z", state="Ogun",
            country="NG", department="CE", faculty="Eng",
            level=300, cgpa=4.0, skills=[], expected_grad_year="2027",
        )
        cls.internship = Internship.objects.create(
            alumnus=cls.alumnus_profile, title="Test", description="d",
            work_mode="Remote", engagement_type="Full-time", location="Remote",
            skills_required=[], duration_weeks=12,
            start_date="2026-01-01", end_date="2026-03-31",
            is_paid=True, stipend=100000, levels=[300],
            company="TC", company_type="Tech", industry="Tech",
            available_slots=5, remaining_slots=5,
        )

    def _make_request(self, user):
        request = self.factory.post("/")
        request.user = user
        return request

    def test_valid_offer_passes_validation(self):
        offer = InternshipOffer.objects.create(
            internship=self.internship, student=self.student_profile
        )
        Serializer = make_student_manage_offer_serializer(InternshipOffer, "internship", Engagement.EngagementType.INTERNSHIP)
        serializer = Serializer(
            data={"offer_id": offer.sqid},
            context={"request": self._make_request(self.student_user)},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_wrong_student_cannot_accept_offer(self):
        offer = InternshipOffer.objects.create(
            internship=self.internship, student=self.student_profile
        )
        Serializer = make_student_manage_offer_serializer(InternshipOffer, "internship", Engagement.EngagementType.INTERNSHIP)
        serializer = Serializer(
            data={"offer_id": offer.sqid},
            context={"request": self._make_request(self.wrong_student_user)},
        )
        self.assertFalse(serializer.is_valid())

    def test_non_pending_offer_fails_validation(self):
        offer = InternshipOffer.objects.create(
            internship=self.internship, student=self.student_profile
        )
        offer.accept()
        Serializer = make_student_manage_offer_serializer(InternshipOffer, "internship", Engagement.EngagementType.INTERNSHIP)
        serializer = Serializer(
            data={"offer_id": offer.sqid},
            context={"request": self._make_request(self.student_user)},
        )
        self.assertFalse(serializer.is_valid())

    def test_inactive_internship_offer_fails(self):
        self.internship.is_active = False
        self.internship.save(update_fields=["is_active"])
        offer = InternshipOffer.objects.create(
            internship=self.internship, student=self.student_profile
        )
        Serializer = make_student_manage_offer_serializer(InternshipOffer, "internship", Engagement.EngagementType.INTERNSHIP)
        serializer = Serializer(
            data={"offer_id": offer.sqid},
            context={"request": self._make_request(self.student_user)},
        )
        self.assertFalse(serializer.is_valid())
        self.internship.is_active = True
        self.internship.save(update_fields=["is_active"])

    def test_already_engaged_student_cannot_accept(self):
        app = InternshipApplication.objects.create(
            internship=self.internship, student=self.student_profile
        )
        create_engagement(
            engagement_type=Engagement.EngagementType.INTERNSHIP,
            student=self.student_profile,
            alumnus=self.alumnus_profile,
            application=app,
        )
        offer = InternshipOffer.objects.create(
            internship=self.internship, student=self.student_profile
        )
        Serializer = make_student_manage_offer_serializer(InternshipOffer, "internship", Engagement.EngagementType.INTERNSHIP)
        serializer = Serializer(
            data={"offer_id": offer.sqid},
            context={"request": self._make_request(self.student_user)},
        )
        self.assertFalse(serializer.is_valid())


class AlumnusManageOfferSerializerFactoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
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
        cls.student_profile = StudentProfile.objects.create(
            user=cls.student_user, phone_num="0803", gender="male",
            firstname="E", lastname="F", address="Z", state="Lagos",
            country="NG", department="CS", faculty="Eng",
            level=300, cgpa=4.0, skills=[], expected_grad_year="2027",
        )
        cls.internship = Internship.objects.create(
            alumnus=cls.alumnus_profile, title="Test", description="d",
            work_mode="Remote", engagement_type="Full-time", location="Remote",
            skills_required=[], duration_weeks=12,
            start_date="2026-01-01", end_date="2026-03-31",
            is_paid=True, stipend=100000, levels=[300],
            company="TC", company_type="Tech", industry="Tech",
            available_slots=5, remaining_slots=5,
        )

    def _make_request(self, user):
        request = self.factory.post("/")
        request.user = user
        return request

    def test_valid_offer_withdraw_passes_validation(self):
        offer = InternshipOffer.objects.create(
            internship=self.internship, student=self.student_profile
        )
        Serializer = make_alumnus_manage_offer_serializer(InternshipOffer, "internship", Engagement.EngagementType.INTERNSHIP)
        serializer = Serializer(
            data={"offer_id": offer.sqid},
            context={"request": self._make_request(self.alumnus_user)},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_other_alumnus_cannot_withdraw_offer(self):
        offer = InternshipOffer.objects.create(
            internship=self.internship, student=self.student_profile
        )
        Serializer = make_alumnus_manage_offer_serializer(InternshipOffer, "internship", Engagement.EngagementType.INTERNSHIP)
        serializer = Serializer(
            data={"offer_id": offer.sqid},
            context={"request": self._make_request(self.other_alumnus_user)},
        )
        self.assertFalse(serializer.is_valid())


class StudentManageApplicationSerializerFactoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.alumnus_user = User.objects.create_user(
            email="alum@test.com", password="p", role=User.Role.ALUMNI, is_active=True
        )
        cls.alumnus_profile = AlumniProfile.objects.create(
            user=cls.alumnus_user, phone_num="0801", gender="male",
            firstname="A", lastname="B", address="X", state="Lagos",
            country="NG", department="CS", faculty="Eng", grad_year="2020",
            current_job_title="SE", current_company="TC", industry="Tech", years_of_exp=3,
        )
        cls.student_user = User.objects.create_user(
            email="stu@test.com", password="p", role=User.Role.STUDENT, is_active=True
        )
        cls.student_profile = StudentProfile.objects.create(
            user=cls.student_user, phone_num="0802", gender="male",
            firstname="C", lastname="D", address="Y", state="Lagos",
            country="NG", department="CS", faculty="Eng",
            level=300, cgpa=4.0, skills=[], expected_grad_year="2027",
        )
        cls.internship = Internship.objects.create(
            alumnus=cls.alumnus_profile, title="Test", description="d",
            work_mode="Remote", engagement_type="Full-time", location="Remote",
            skills_required=[], duration_weeks=12,
            start_date="2026-01-01", end_date="2026-03-31",
            is_paid=True, stipend=100000, levels=[300],
            company="TC", company_type="Tech", industry="Tech",
            available_slots=5, remaining_slots=5,
        )

    def _make_request(self, user):
        request = self.factory.post("/")
        request.user = user
        return request

    def test_valid_withdraw_passes_validation(self):
        app = InternshipApplication.objects.create(
            internship=self.internship, student=self.student_profile
        )
        Serializer = make_student_manage_application_serializer(
            InternshipApplication, "internship", Engagement.EngagementType.INTERNSHIP
        )
        serializer = Serializer(
            data={"application_id": app.sqid},
            context={"request": self._make_request(self.student_user)},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_non_pending_application_fails(self):
        app = InternshipApplication.objects.create(
            internship=self.internship, student=self.student_profile
        )
        app.accept()
        Serializer = make_student_manage_application_serializer(
            InternshipApplication, "internship", Engagement.EngagementType.INTERNSHIP
        )
        serializer = Serializer(
            data={"application_id": app.sqid},
            context={"request": self._make_request(self.student_user)},
        )
        self.assertFalse(serializer.is_valid())


class AlumnusManageApplicationSerializerFactoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
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
        cls.student_profile = StudentProfile.objects.create(
            user=cls.student_user, phone_num="0803", gender="male",
            firstname="E", lastname="F", address="Z", state="Lagos",
            country="NG", department="CS", faculty="Eng",
            level=300, cgpa=4.0, skills=[], expected_grad_year="2027",
        )
        cls.internship = Internship.objects.create(
            alumnus=cls.alumnus_profile, title="Test", description="d",
            work_mode="Remote", engagement_type="Full-time", location="Remote",
            skills_required=[], duration_weeks=12,
            start_date="2026-01-01", end_date="2026-03-31",
            is_paid=True, stipend=100000, levels=[300],
            company="TC", company_type="Tech", industry="Tech",
            available_slots=5, remaining_slots=5,
        )

    def _make_request(self, user):
        request = self.factory.post("/")
        request.user = user
        return request

    def test_valid_accept_passes_validation(self):
        app = InternshipApplication.objects.create(
            internship=self.internship, student=self.student_profile
        )
        Serializer = make_alumnus_manage_application_serializer(
            InternshipApplication, "internship", Engagement.EngagementType.INTERNSHIP
        )
        serializer = Serializer(
            data={"application_id": app.sqid},
            context={"request": self._make_request(self.alumnus_user)},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_other_alumnus_cannot_manage_application(self):
        app = InternshipApplication.objects.create(
            internship=self.internship, student=self.student_profile
        )
        Serializer = make_alumnus_manage_application_serializer(
            InternshipApplication, "internship", Engagement.EngagementType.INTERNSHIP
        )
        serializer = Serializer(
            data={"application_id": app.sqid},
            context={"request": self._make_request(self.other_alumnus_user)},
        )
        self.assertFalse(serializer.is_valid())
