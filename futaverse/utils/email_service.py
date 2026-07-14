import logging
import os

from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail

logger = logging.getLogger(__name__)


class BrevoEmailError(Exception):
    """Raised when an email send fails. Caller decides how to handle."""


class BrevoEmailService:
    def __init__(self):
        self.configuration = Configuration()
        self.configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")
        self.api_instance = TransactionalEmailsApi(ApiClient(self.configuration))

    def send(self, subject: str, body: str, recipient: str, sender_name="FutaVerse Services", sender_email=None, is_html=False) -> None:
        sender_email = sender_email or os.getenv("MAIL_USERNAME")
        content_field = "html_content" if is_html else "text_content"

        email_data = {
            "to": [{"email": recipient}],
            "sender": {"email": sender_email, "name": sender_name},
            "subject": subject,
            content_field: body,
        }
        email = SendSmtpEmail(**email_data)

        try:
            self.api_instance.send_transac_email(email)
        except Exception as e:
            logger.error("Email send failed: %s", e)
            raise BrevoEmailError(f"Email send failed: {e}") from e

    def send_bulk(self, subject: str, body: str, recipients: list, is_html=True) -> None:
        sender_email = os.getenv("MAIL_USERNAME")
        content_field = "html_content" if is_html else "text_content"

        message_versions = [
            {"to": [{"email": email}]} for email in recipients
        ]

        email_data = {
            "sender": {"email": sender_email, "name": "FutaVerse Services"},
            "subject": subject,
            content_field: body,
            "message_versions": message_versions,
        }
        email = SendSmtpEmail(**email_data)

        try:
            self.api_instance.send_transac_email(email)
        except Exception as e:
            logger.error("Bulk email send failed: %s", e)
            raise BrevoEmailError(f"Bulk email send failed: {e}") from e
