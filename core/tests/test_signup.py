from unittest.mock import patch

from rest_framework import status

from core.models import User
from futaverse.tests_helpers import BaseAPITestCase


class InactiveUserReSignupTests(BaseAPITestCase):
    """Locks in B8 behavior: inactive user with same email is hard-deleted before re-signup."""

    def _signup_payload(self, email):
        return {
            "email": email,
            "password": "testpass123",
            "profile": {
                "phone_num": "08012345678",
                "gender": "male",
                "firstname": "New",
                "lastname": "Student",
                "address": "1 Test St",
                "state": "Lagos",
                "country": "Nigeria",
                "department": "CS",
                "faculty": "Eng",
                "level": 300,
                "cgpa": "4.50",
                "skills": [],
                "expected_grad_year": "2027",
            },
        }

    @patch("core.views.mailer.send")
    def test_re_signup_with_inactive_user_email_succeeds(self, mock_send):
        User.objects.create_user(
            email="reuse@test.com",
            password="oldpass",
            role=User.Role.STUDENT,
            is_active=False,
        )

        resp = self.client.post(
            "/api/auth/signup/student",
            self._signup_payload("reuse@test.com"),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        users = User.objects.filter(email="reuse@test.com")
        self.assertEqual(users.count(), 1, "Inactive user should be deleted, then new one created")
