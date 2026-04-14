from django.urls import path

from .webhooks import PaystackWebhookView
from .views import ListBanksView, ResolveAccountView

urlpatterns = [
    path('/paystack_webhook', PaystackWebhookView.as_view(), name='paystack-webhook'),
    path('/banks', ListBanksView.as_view(), name="list-paystack-banks"),
    path('/resolve', ResolveAccountView.as_view(), name="resolve-account"),
]