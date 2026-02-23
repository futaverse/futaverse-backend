from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from .models import Internship, InternshipApplication, InternshipOffer, ApplicationResume, InternshipEngagement
from .serializers import InternshipSerializer, InternshipStatusSerializer, InternshipOfferSerializer, InternshipApplicationSerializer, ApplicationResumeSerializer, InternshipEngagementSerializer
from .mixins import OfferValidationMixin, ApplicationValidationMixin

from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent
from futaverse.utils.supabase import upload_file_to_supabase

@extend_schema(tags=['Internships'], summary="List (GET) and create (POST) internships (alumnus)")
class ListCreateInternshipView(generics.ListCreateAPIView):
    serializer_class = InternshipSerializer
    permission_classes = [IsAuthenticatedAlumnus]
    
    def get_queryset(self):
        user = self.request.user
        return Internship.objects.filter(alumnus=user.alumni_profile).select_related('alumnus').order_by('-created_at')
    
    def perform_create(self, serializer):
        alumnus = self.request.user.alumni_profile
        serializer.save(alumnus=alumnus)

@extend_schema(tags=['Internships'], summary='Retrieve (GET), update (PATCH) and delete (DELETE) an internship by id (alumnus)') 
class RetrieveUpdateDestroyMentorshipView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InternshipSerializer
    http_method_names = ['patch', 'get', 'delete']
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    
    def get_queryset(self):
        user = self.request.user
        return Internship.objects.filter(alumnus=user.alumni_profile).select_related('alumnus')
    
    def perform_destroy(self, instance):
        instance.soft_delete()
    
@extend_schema(tags=['Internships'], summary='Toggle internship active status (alumnus)')
class ToggleInternshipActiveView(generics.UpdateAPIView):
    queryset = Internship.objects.all()
    serializer_class = InternshipStatusSerializer
    http_method_names = ['patch']
    permission_classes = [IsAuthenticatedAlumnus]
    
    def perform_update(self, serializer):
        internship = self.get_object()
        internship.toggle_active()
        
@extend_schema(tags=['Internship Offers'], summary='Create an internship offer (alumnus)')
class CreateInternshipOfferView(generics.CreateAPIView):
    serializer_class = InternshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus]
    
    # TODO: Send notification to student when an offer is created 
    
@extend_schema(tags=['Internship Offers'], summary='List internship offers (alumnus and student)')
class ListInternshipOfferView(generics.ListAPIView):
    serializer_class = InternshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    
    def get_queryset(self):
        user = self.request.user
        print(user)
        
        if user.role == User.Role.ALUMNI:
            return InternshipOffer.objects.filter(internship__alumnus=user.alumni_profile).select_related('internship', 'student').order_by('-created_at')
        
        elif user.role == User.Role.STUDENT:
            return InternshipOffer.objects.filter(student=user.student_profile).select_related('internship', 'student').order_by('-created_at')
        
        return InternshipOffer.objects.none()
    
@extend_schema(tags=['Internship Offers'], summary='Retrieve an internship offer by id (alumnus and student)')
class RetrieveInternshipOfferView(generics.RetrieveAPIView):
    serializer_class = InternshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return InternshipOffer.objects.filter(internship__alumnus=user.alumni_profile).select_related('internship', 'student', 'internship__alumnus')
        
        elif user.role == User.Role.STUDENT:
            return InternshipOffer.objects.filter(student=user.student_profile).select_related('internship', 'student')
        
        return InternshipOffer.objects.none()
    
@extend_schema(tags=['Internship Offers'], summary='Accept an internship offer (student)')
class AcceptInternshipOfferView(OfferValidationMixin, APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        offer = self.get_offer()
        
        internship = offer.internship
        student = offer.student
        alumnus = internship.alumnus
        
        if offer.student != request.user.student_profile:
            return Response({"detail": "You are not authorized to accept this internship offer."}, status=status.HTTP_403_FORBIDDEN)
        
        if InternshipEngagement.objects.filter(internship=internship, student=student).exists():
            return Response({"detail": "You are already engaged in this internship."}, status=status.HTTP_400_BAD_REQUEST)
        
        engagement = InternshipEngagement.objects.create(
            internship=internship,
            student=student,
            alumnus= alumnus,
            source= InternshipEngagement.Source.OFFER,
            source_id= offer.id,
        )
        
        offer.accept()
        internship.decrement_remaining_slots()
        return Response({"detail": "Offer accepted successfully.", "engagement_id": engagement.id},status=status.HTTP_201_CREATED)
    
@extend_schema(tags=['Internship Offers'], summary='Reject an internship offer (student)')
class RejectInternshipOfferView(OfferValidationMixin, APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        offer = self.get_offer()
        
        if offer.student != request.user.student_profile:
            return Response({"detail": "You are not authorized to reject this internship."}, status=status.HTTP_403_FORBIDDEN)
        
        offer.reject()
        
        return Response({"detail": "Application rejected successfully."}, status=status.HTTP_200_OK)
    
@extend_schema(tags=['Internship Offers'], summary='Withdraw an internship offer (alumnus)')
class WithdrawInternshipOfferView(OfferValidationMixin, APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        offer = self.get_offer()
        
        if offer.internship.alumnus != request.user.alumni_profile:
            return Response({"detail": "You are not authorized to withdraw this application."}, status=status.HTTP_403_FORBIDDEN)
        
        offer.withdraw()
        
        return Response({"detail": "Offer withdrawn successfully."},status=status.HTTP_200_OK)
    
@extend_schema(tags=['Internship Applications'], summary='Apply for an internship (student)')
class CreateInternshipApplication(generics.CreateAPIView):
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
        
        if user.role == User.Role.ALUMNI:
            return InternshipApplication.objects.filter(internship__alumnus=user.alumni_profile).select_related('internship', 'student', 'resume').order_by('-created_at')
        
        elif user.role == User.Role.STUDENT:
            return InternshipApplication.objects.filter(student=user.student_profile).select_related('internship', 'resume', 'student').order_by('-created_at')
        
        return InternshipApplication.objects.none()
    
@extend_schema(tags=['Internship Applications'], summary='Retrieve an internship application by id (alumnus and student)')
class RetrieveInternshipApplicationView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = InternshipApplicationSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return InternshipApplication.objects.filter(internship__alumnus=user.alumni_profile).select_related('internship', 'student', 'Internship__alumnus')
        
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
class AcceptInternshipApplicationView(ApplicationValidationMixin, APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        application = self.get_application()
        
        internship = application.internship
        student = application.student
        alumnus = internship.alumnus
        
        if alumnus != request.user.alumni_profile:
            return Response({"detail": "You are not authorized to manage this internship."}, status=status.HTTP_403_FORBIDDEN)
        
        if InternshipEngagement.objects.filter(internship=internship, student=student).exists():
            return Response({"detail": "This student is already engaged in this internship."}, status=status.HTTP_400_BAD_REQUEST)
        
        engagement = InternshipEngagement.objects.create(
            internship=internship,
            student=student,
            alumnus= alumnus,
            source=InternshipEngagement.Source.APPLICATION,
            source_id=application.id,
        )
        
        application.accept()
        internship.decrement_remaining_slots()
        return Response({"detail": "Application accepted successfully.", "engagement_id": engagement.id},status=status.HTTP_201_CREATED)
    
@extend_schema(tags=['Internship Applications'], summary='Reject an internship application (alumnus)')
class RejectInternshipApplicationView(ApplicationValidationMixin, APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        application = self.get_application()
        
        internship = application.internship
        
        if internship.alumnus != request.user.alumni_profile:
            return Response({"detail": "You are not authorized to manage this internship."}, status=status.HTTP_403_FORBIDDEN)
        
        application.reject()
        
        return Response({"detail": "Application rejected successfully."},status=status.HTTP_200_OK)
    
@extend_schema(tags=['Internship Applications'], summary='Withdraw an internship application (student)')
class WithdrawInternshipApplicationView(ApplicationValidationMixin, APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        application = self.get_application()
        
        if application.student != request.user.student_profile:
            return Response({"detail": "You are not authorized to withdraw this application."}, status=status.HTTP_403_FORBIDDEN)
        
        application.withdraw()
        
        return Response({"detail": "Application withdrawn successfully."},status=status.HTTP_200_OK)
    
@extend_schema(tags=['Internship Engagements'], summary='List all internship engagements (alumnus and student)')
class ListInternshipEngagementsView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = InternshipEngagementSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return InternshipEngagement.objects.filter(alumnus=user.alumni_profile).select_related('internship', 'student', 'alumnus')
        
        elif user.role == User.Role.STUDENT:
            return InternshipEngagement.objects.filter(student=user.student_profile).select_related('internship', 'student', 'alumnus')
        
        return InternshipEngagement.objects.none()
    
@extend_schema(tags=['Internship Engagements'], summary='Retrieve an internship engagement by id (alumnus and student)')
class RetrieveInternshipEngagementView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = InternshipEngagementSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return InternshipEngagement.objects.filter(alumnus=user.alumni_profile).select_related('Internship', 'student', 'alumnus')
        
        elif user.role == User.Role.STUDENT:
            return InternshipEngagement.objects.filter(student=user.student_profile).select_related('Internship', 'student')
        
        return InternshipEngagement.objects.none()