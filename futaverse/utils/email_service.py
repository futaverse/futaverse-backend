from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail
import os
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

class BrevoEmailService:
    def __init__(self):
        self.configuration = Configuration()
        self.configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")
        self.api_instance = TransactionalEmailsApi(ApiClient(self.configuration))

    def send(self, subject: str, body: str, recipient: str, sender_name="FutaVerse Services", sender_email=None, is_html=False,):
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
            print(f"Email send failed: {e}")
            return Response({"detail": str(e), "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
    def send_bulk(self, subject: str, body: str, recipients: list, is_html=True):
        """
        recipients: list of strings ['a@b.com', 'c@d.com']
        """
        sender_email = os.getenv("MAIL_USERNAME")
        content_field = "html_content" if is_html else "text_content"

        message_versions = [
            {"to": [{"email": email}]} for email in recipients
        ]

        email_data = {
            "sender": {"email": sender_email, "name": "FutaVerse Services"},
            "subject": subject,
            content_field: body,
            "message_versions": message_versions
        }
        
        email = SendSmtpEmail(**email_data)
        
        try:
            self.api_instance.send_transac_email(email)
        except Exception as e:
            logger.error(f"Bulk Email send failed: {e}")