from unittest.mock import patch, MagicMock

from django.test import TestCase

from futaverse.utils.email_service import BrevoEmailService, BrevoEmailError


class BrevoEmailServiceContractTests(TestCase):
    """Locks in Sub-Project 3 fix: send() returns None on success, raises on failure."""

    def setUp(self):
        self.service = BrevoEmailService()
        self.service.api_instance = MagicMock()

    def test_send_returns_none_on_success(self):
        self.service.api_instance.send_transac_email.return_value = {"messageId": "ok"}
        result = self.service.send(
            subject="Test",
            body="body",
            recipient="test@example.com",
        )
        self.assertIsNone(result)

    def test_send_raises_brevo_email_error_on_failure(self):
        from sib_api_v3_sdk.rest import ApiException
        self.service.api_instance.send_transac_email.side_effect = ApiException(status=500, reason="err")
        with self.assertRaises(BrevoEmailError):
            self.service.send(
                subject="Test",
                body="body",
                recipient="test@example.com",
            )

    def test_send_does_not_return_drf_response(self):
        from rest_framework.response import Response
        self.service.api_instance.send_transac_email.return_value = {"messageId": "ok"}
        result = self.service.send(
            subject="Test",
            body="body",
            recipient="test@example.com",
        )
        self.assertNotIsInstance(result, Response)

    def test_send_bulk_returns_none_on_success(self):
        self.service.api_instance.send_transac_email.return_value = {"messageId": "ok"}
        result = self.service.send_bulk(
            subject="Test",
            body="body",
            recipients=["a@example.com", "b@example.com"],
        )
        self.assertIsNone(result)

    def test_send_bulk_raises_brevo_email_error_on_failure(self):
        from sib_api_v3_sdk.rest import ApiException
        self.service.api_instance.send_transac_email.side_effect = ApiException(status=500, reason="err")
        with self.assertRaises(BrevoEmailError):
            self.service.send_bulk(
                subject="Test",
                body="body",
                recipients=["a@example.com"],
            )
