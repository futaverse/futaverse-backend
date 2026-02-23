from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

import hmac
import hashlib
import os
import json

from drf_spectacular.utils import extend_schema

from .webhookshandler import handle_charge_success

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_TEST_SECRET_KEY")

@extend_schema(tags=["Payments"], summary="Paystack Webhook Endpoint")
class PaystackWebhookView(APIView):
    authentication_classes = []  
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        payload = request.body
        signature = request.headers.get('x-paystack-signature')
        
        hashed = hmac.new(
            PAYSTACK_SECRET_KEY.encode(),
            msg=payload,
            digestmod=hashlib.sha512
        ).hexdigest()
        
        if hashed != signature:
            return Response({"detail": "Invalid signature"}, status=403)
        
        event = json.loads(payload)
        event_type = event.get("event")
        data = event.get("data", {})
        
        print("Received event:", event_type)
        print("Data:", data)
        
        if event_type == "charge.success":
            handle_charge_success(data)
            
        return Response({"status": "ok"}, status=200)
