from django.urls import path

from .webhooks import PaystackWebhookView

urlpatterns = [
    path('/paystack_webhook', PaystackWebhookView.as_view(), name='paystack-webhook'),
]