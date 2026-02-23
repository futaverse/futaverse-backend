from django.db import transaction

from rest_framework import generics, status
from drf_spectacular.utils import extend_schema

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from core.models import User, OTP
from .serializers import CreateStudentSerializer, StudentResumeSerializer
from .models import StudentResume

from futaverse.views import PublicGenericAPIView
from futaverse.utils.email_service import BrevoEmailService
from futaverse.extensions import upload_resume

mailer = BrevoEmailService()

@extend_schema(tags=['Auth'])
class CreateStudentView(generics.CreateAPIView, PublicGenericAPIView):
    serializer_class = CreateStudentSerializer
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        
        existing_inactive_user = User.objects.filter(email=email, is_active=False).first()
        if existing_inactive_user:
            existing_inactive_user.delete()  

        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        with transaction.atomic():
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
        
@extend_schema(tags=['Students'])
class UploadResumeView(generics.CreateAPIView):
    queryset = StudentResume.objects.all()
    serializer_class = StudentResumeSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request, *args, **kwargs):
        user = request.user
        resume = request.FILES.get('resume')
        
        if not resume:
            return Response({"detail": "Resume not provided", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        public_url = upload_resume(resume, user.student_profile.id)
        
        serializer = self.get_serializer(data={"resume": public_url, "student": user.student_profile.id, "filename": resume.name})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)