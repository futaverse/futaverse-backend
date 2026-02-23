from rest_framework import generics
from drf_spectacular.utils import extend_schema

from core.models import User, OTP
from .serializers import CreateAlumnusSerializer

from alumnus.serializers import CreateAlumnusSerializer
from futaverse.views import PublicGenericAPIView
from futaverse.utils.email_service import BrevoEmailService

mailer = BrevoEmailService()

@extend_schema(tags=['Auth'])
class CreateAlumnusView(generics.CreateAPIView, PublicGenericAPIView):
    serializer_class = CreateAlumnusSerializer
    
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        
        existing_inactive_user = User.objects.filter(email=email, is_active=False).first()
        if existing_inactive_user:
            existing_inactive_user.delete()  

        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        user = serializer.save()
        otp = OTP.generate_otp(user)
        
        mailer.send(
            subject="Verify your email",
            body=(
                f"Enter the OTP below into the required field \n"
                f"The OTP will expire in 10 mins\n\n"
                f"OTP: {otp}\n\n"
                f"If you did not initiate this request, please contact .................com\n\n"
                f"From the FutaVerse Team"
            ),
            recipient=user.email,
        )