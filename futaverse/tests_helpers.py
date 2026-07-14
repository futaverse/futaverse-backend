from datetime import date

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import User, StudentProfile, AlumniProfile


class BaseAPITestCase(APITestCase):
    def _create_user(self, email, role, **kwargs):
        user = User.objects.create_user(
            email=email,
            password="testpass123",
            role=role,
            is_active=True,
            **kwargs,
        )
        return user

    def _create_student(self, email="student@test.com", **profile_kwargs):
        user = self._create_user(email, User.Role.STUDENT)
        defaults = dict(
            phone_num="08012345678",
            gender="male",
            firstname="Test",
            lastname="Student",
            address="123 Test St",
            state="Lagos",
            country="Nigeria",
            department="Computer Science",
            faculty="Engineering",
            level=300,
            cgpa=4.50,
            skills=["python", "django"],
            expected_grad_year="2027",
        )
        defaults.update(profile_kwargs)
        StudentProfile.objects.create(user=user, **defaults)
        return user

    def _create_alumnus(self, email="alumnus@test.com", **profile_kwargs):
        user = self._create_user(email, User.Role.ALUMNI)
        defaults = dict(
            phone_num="08098765432",
            gender="male",
            firstname="Test",
            lastname="Alumnus",
            address="456 Test Ave",
            state="Ogun",
            country="Nigeria",
            department="Computer Science",
            faculty="Engineering",
            grad_year="2020",
            current_job_title="Software Engineer",
            current_company="Tech Corp",
            industry="Technology",
            years_of_exp=5,
        )
        defaults.update(profile_kwargs)
        AlumniProfile.objects.create(user=user, **defaults)
        return user

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

    def make_internship(self, alumnus_user, **kwargs):
        from internships.models import Internship
        defaults = dict(
            title="Software Engineer Intern",
            description="Build stuff",
            work_mode="Remote",
            engagement_type="Full-time",
            location="Lagos",
            skills_required=["python"],
            duration_weeks=12,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            is_paid=True,
            stipend=100000,
            levels=[300],
            company="Tech Corp",
            company_type="Tech",
            industry="Tech",
            available_slots=5,
            remaining_slots=5,
        )
        defaults.update(kwargs)
        return Internship.objects.create(alumnus=alumnus_user.alumni_profile, **defaults)

    def make_mentorship(self, alumnus_user, **kwargs):
        from mentorships.models import Mentorship
        from mentorships.models import MentorshipCategory
        defaults = dict(
            title="Career Mentorship",
            description="Guidance",
            category=MentorshipCategory.CAREER_DEVELOPMENT,
            focus_areas=["career_guidance"],
            work_mode="Remote",
            duration_weeks=8,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28),
            available_slots=3,
            remaining_slots=3,
            is_active=True,
        )
        defaults.update(kwargs)
        return Mentorship.objects.create(alumnus=alumnus_user.alumni_profile, **defaults)

    def make_engagement(self, engagement_model, *, student_user, alumnus_user, **kwargs):
        defaults = dict(
            student=student_user.student_profile,
            alumnus=alumnus_user.alumni_profile,
            source="application",
            source_id=1,
            status="active",
        )
        defaults.update(kwargs)
        return engagement_model.objects.create(**defaults)

    def make_application(self, application_model, *, student_user, **kwargs):
        from engagements.models import EngagementLifecycleStatus
        defaults = dict(
            student=student_user.student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )
        defaults.update(kwargs)
        return application_model.objects.create(**defaults)

    def make_offer(self, offer_model, *, student_user, **kwargs):
        from engagements.models import EngagementLifecycleStatus
        defaults = dict(
            student=student_user.student_profile,
            status=EngagementLifecycleStatus.PENDING,
        )
        defaults.update(kwargs)
        return offer_model.objects.create(**defaults)
