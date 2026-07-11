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
