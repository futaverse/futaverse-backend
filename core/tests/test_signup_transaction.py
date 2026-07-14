from unittest.mock import patch

from rest_framework import status

from core.models import User
from futaverse.tests_helpers import BaseAPITestCase


class SignupTransactionTests(BaseAPITestCase):
    """Locks in Task 5 fix: mailer.send must run OUTSIDE the DB transaction."""

    def _payload(self, email):
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
                "skills": ["python"],
                "expected_grad_year": "2027",
            },
        }

    @patch("core.views.mailer.send")
    def test_user_and_otp_are_created_on_successful_signup(self, mock_send):
        resp = self.client.post(
            "/api/auth/signup/student",
            self._payload("newstudent@test.com"),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="newstudent@test.com")
        self.assertTrue(hasattr(user, "otp"))
        self.assertFalse(user.otp.verified)
        mock_send.assert_called_once()

    @patch("core.views.mailer.send")
    def test_email_send_failure_does_not_roll_back_user(self, mock_send):
        """Locks in Task 5 fix: if email send raises, the user record is still saved."""
        mock_send.side_effect = Exception("Brevo API down")

        try:
            self.client.post(
                "/api/auth/signup/student",
                self._payload("newstudent2@test.com"),
                format="json",
            )
        except Exception:
            pass

        self.assertTrue(
            User.objects.filter(email="newstudent2@test.com").exists(),
            "User should be created before email send is attempted",
        )
