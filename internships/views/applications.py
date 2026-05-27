from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from internships.models import InternshipApplication, ApplicationResume, InternshipEngagement, InternshipStatus
from internships.serializers import InternshipApplicationSerializer, ApplicationResumeSerializer, ManageInternshipApplicationSerializer, InternshipEngagementSerializer
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent
from futaverse.utils.supabase import upload_file_to_supabase

@extend_schema(tags=['Internship Applications'], summary='Apply for an internship (student)')
class CreateInternshipApplicationView(generics.CreateAPIView):
    serializer_class = InternshipApplicationSerializer
    permission_classes = [IsAuthenticatedStudent]
    
    @transaction.atomic
    def perform_create(self, serializer):
        resume = serializer.validated_data.pop('resume', None)
        student = self.request.user.student_profile
        
        application = serializer.save(student=student)
        
        if resume:
            resume.application = application
            resume.save(update_fields=['application'])
        
    # TODO: Send notification to alumni when an application is submitted 
    
@extend_schema(tags=['Internship Applications'], summary='List all internship applications (alumnus and student)')
class ListInternshipApplicationsView(generics.ListAPIView):
    serializer_class = InternshipApplicationSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    
    def get_queryset(self):
        user = self.request.user
        
        # Only applications that have not been accepted or rejected
        if user.role == User.Role.ALUMNI:
            return InternshipApplication.objects.filter(internship__alumnus=user.alumni_profile, status=InternshipStatus.PENDING).select_related('internship', 'student', 'resume').order_by('-created_at')
        
        elif user.role == User.Role.STUDENT:
            return InternshipApplication.objects.filter(student=user.student_profile, status=InternshipStatus.PENDING).select_related('internship', 'resume', 'student').order_by('-created_at')
        
        return InternshipApplication.objects.none()
    
@extend_schema(tags=['Internship Applications'], summary='Retrieve an internship application by id (alumnus and student)')
class RetrieveInternshipApplicationView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = InternshipApplicationSerializer
    lookup_field = 'sqid'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return InternshipApplication.objects.filter(internship__alumnus=user.alumni_profile).select_related('internship', 'student', 'internship__alumnus')
        
        elif user.role == User.Role.STUDENT:
            return InternshipApplication.objects.filter(student=user.student_profile).select_related('internship', 'student')
        
        return InternshipApplication.objects.none()
        
@extend_schema(tags=['Internship Applications'], summary='Upload a resume for an internship application (student)')
class UploadApplicationResumeView(generics.CreateAPIView):
    queryset = ApplicationResume.objects.all()
    serializer_class = ApplicationResumeSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticatedStudent]
    
    def create(self, request, *args, **kwargs):
        resume = request.FILES.get('resume')
        student = request.user.student_profile
        
        if not resume:
            return Response({"detail": "Resume not provided", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        resume_url = upload_file_to_supabase(resume, 'application_resumes/')
        
        serializer = self.get_serializer(data={'resume': resume_url})
        serializer.is_valid(raise_exception=True)
        serializer.save(student=student)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
@extend_schema(tags=['Internship Applications'], summary='Accept an internship application (alumnus)')
class AcceptInternshipApplicationView(APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = ManageInternshipApplicationSerializer(
            data={"application_id": kwargs.get("application_id")},
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]
        
        internship = application.internship
        student = application.student
        alumnus = internship.alumnus
        
        engagement = InternshipEngagement.objects.create(
            internship=internship,
            student=student,
            alumnus= alumnus,
            source=InternshipEngagement.Source.APPLICATION,
            source_id=application.id,
        )
        
        application.accept()
        internship.decrement_remaining_slots()
        
        return Response({"detail": "Application accepted successfully.", "engagement": InternshipEngagementSerializer(engagement).data},status=status.HTTP_201_CREATED)
    
@extend_schema(tags=['Internship Applications'], summary='Reject an internship application (alumnus)')
class RejectInternshipApplicationView(APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        serializer = ManageInternshipApplicationSerializer(
            data={"application_id": kwargs.get("application_id")},
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]
        
        application.reject()
        
        return Response({"detail": "Application rejected successfully."},status=status.HTTP_200_OK)
    
@extend_schema(tags=['Internship Applications'], summary='Withdraw an internship application (student)')
class WithdrawInternshipApplicationView(APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        serializer = ManageInternshipApplicationSerializer(
            data={"application_id": kwargs.get("application_id")},
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]
        
        application.withdraw()
        
        return Response({"detail": "Application withdrawn successfully."},status=status.HTTP_200_OK)