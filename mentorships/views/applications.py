from django.db import transaction

from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from mentorships.models import MentorshipEngagement, MentorshipApplication, MentorshipStatus
from mentorships.serializers import  MentorshipApplicationSerializer, ManagementorshipApplicationSerializer, MentorshipEngagementSerializer
from mentorships.mixins import ApplicationValidationMixin
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

@extend_schema(tags=['Mentorship Applications'], summary='Apply for a mentorship (student)')
class CreateMentorshipApplicationView(generics.CreateAPIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = MentorshipApplicationSerializer
    
    def perform_create(self, serializer):
        student = self.request.user.student_profile
        serializer.save(student=student)
    
@extend_schema(tags=['Mentorship Applications'], summary='List mentorship applications (alumnus and student)')
class ListMentorshipApplicationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipApplicationSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return MentorshipApplication.objects.filter(mentorship__alumnus=user.alumni_profile, status=MentorshipStatus.PENDING).select_related('mentorship', 'student', 'mentorship__alumnus')
        
        elif user.role == User.Role.STUDENT:
            return MentorshipApplication.objects.filter(student=user.student_profile, status=MentorshipStatus.PENDING).select_related('mentorship', 'student')
        
        return MentorshipApplication.objects.none()
        
@extend_schema(tags=['Mentorship Applications'], summary='Retrieve a mentorship application by id (alumnus and student)')
class RetrieveMentorshipApplicationView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipApplicationSerializer
    lookup_field = 'sqid'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return MentorshipApplication.objects.filter(mentorship__alumnus=user.alumni_profile).select_related('mentorship', 'student', 'mentorship__alumnus')
        
        elif user.role == User.Role.STUDENT:
            return MentorshipApplication.objects.filter(student=user.student_profile).select_related('mentorship', 'student')
        
        return MentorshipApplication.objects.none()
    
@extend_schema(tags=['Mentorship Applications'], summary='Accept a mentorship application (alumnus)')
class AcceptMentorshipApplicationView(ApplicationValidationMixin, APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = ManagementorshipApplicationSerializer(
            data={"application_id": kwargs.get("application_id")},
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]
        
        mentorship = application.mentorship
        student = application.student
        alumnus = mentorship.alumnus
        
        engagement = MentorshipEngagement.objects.create(
            mentorship=mentorship,
            student=student,
            alumnus= alumnus,
            source=MentorshipEngagement.Source.APPLICATION,
            source_id=application.id,
        )
        
        application.accept()
        mentorship.decrement_remaining_slots()
        return Response({"detail": "Application accepted successfully.", "engagement": MentorshipEngagementSerializer(engagement).data},status=status.HTTP_201_CREATED)
    
@extend_schema(tags=['Mentorship Applications'], summary='Reject a mentorship application (alumnus)')
class RejectMentorshipApplicationView(ApplicationValidationMixin, APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        serializer = ManagementorshipApplicationSerializer(
            data={"application_id": kwargs.get("application_id")},
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]
        
        application.reject()
        
        return Response({"detail": "Application rejected successfully."},status=status.HTTP_200_OK)
    
@extend_schema(tags=['Mentorship Applications'], summary='Withdraw a mentorship application (student)')
class WithdrawMentorshipApplicationView(ApplicationValidationMixin, APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        serializer = ManagementorshipApplicationSerializer(
            data={"application_id": kwargs.get("application_id")},
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]
        
        application.withdraw()
        
        return Response({"detail": "Application withdrawn successfully."},status=status.HTTP_200_OK)