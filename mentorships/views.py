from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import filters, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from .models import Mentorship, MentorshipOffer, MentorshipEngagement, MentorshipApplication
from .serializers import MentorshipSerializer, MentorshipOfferSerializer, MentorshipApplicationSerializer, MentorshipStatusSerializer, MentorshipEngagementSerializer
from .mixins import OfferValidationMixin, ApplicationValidationMixin
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

@extend_schema(tags=['Mentorships'], summary='List (GET) and create (POST) mentorships (alumnus)')
class ListCreateMentorshipView(generics.ListCreateAPIView):
    serializer_class = MentorshipSerializer
    permission_classes = [IsAuthenticatedAlumnus]
    
    def get_queryset(self):
        user = self.request.user
        return Mentorship.objects.filter(alumnus=user.alumni_profile).select_related('alumnus')
    
    def perform_create(self, serializer):
        alumnus = self.request.user.alumni_profile
        serializer.save(alumnus=alumnus)

@extend_schema(tags=['Mentorships'], summary='Retrieve (GET), update (PATCH) and delete (DELETE) a mentorship by id (alumnus)')
class RetrieveUpdateDestroyMentorshipView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MentorshipSerializer
    permission_classes = [IsAuthenticatedAlumnus]
    http_method_names = ['get', 'patch', 'delete']
    
    def get_queryset(self):
        user = self.request.user
        return Mentorship.objects.filter(alumnus=user.alumni_profile).select_related('alumnus')
    
    def perform_destroy(self, instance):
        instance.soft_delete()
        
@extend_schema(tags=['Mentorships'], summary='Toggle active status of a mentorship (alumnus)')
class ToggleMentorshipActiveView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedAlumnus]
    queryset = Mentorship.objects.all()
    serializer_class = MentorshipStatusSerializer
    http_method_names = ['patch']
    
    def perform_update(self, serializer):
        mentorship = self.get_object()
        mentorship.toggle_active()
    
@extend_schema(tags=['Mentorship Offers'], summary='Create a mentorship offer (alumnus)')
class CreateMentorshipOfferView(generics.CreateAPIView):
    serializer_class = MentorshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus]
    
@extend_schema(tags=['Mentorship Offers'], summary='List mentorship offers (alumnus and student)')
class ListMentorshipOfferView(generics.ListAPIView):
    serializer_class = MentorshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return MentorshipOffer.objects.filter(mentorship__alumnus=user.alumni_profile).select_related('mentorship', 'student').order_by('-created_at')
        
        elif user.role == User.Role.STUDENT:
            return MentorshipOffer.objects.filter(student=user.student_profile).select_related('mentorship', 'student').order_by('-created_at')
        
        return MentorshipOffer.objects.none()
        
@extend_schema(tags=['Mentorship Offers'], summary='Retrieve a mentorship offer by id (alumnus and student)')
class RetrieveMentorshipOfferView(generics.RetrieveAPIView):
    serializer_class = MentorshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return MentorshipOffer.objects.filter(mentorship__alumnus=user.alumni_profile).select_related('mentorship', 'student', 'mentorship__alumnus')
        
        elif user.role == User.Role.STUDENT:
            return MentorshipOffer.objects.filter(student=user.student_profile).select_related('mentorship', 'student')
        
        return MentorshipOffer.objects.none()
        
@extend_schema(tags=['Mentorship Offers'], summary='Accept a mentorship offer (student)')
class AcceptOfferView(OfferValidationMixin, APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        offer = self.get_offer()
        
        mentorship = offer.mentorship
        student = offer.student
        alumnus = mentorship.alumnus
        
        if student != request.user.student_profile:
            return Response({"detail": "You are not authorized to accept this mentorship offer."}, status=status.HTTP_403_FORBIDDEN)
        
        if MentorshipEngagement.objects.filter(mentorship=mentorship, student=student).exists():
            return Response({"detail": "You are already engaged in this mentorship."}, status=status.HTTP_400_BAD_REQUEST)
        
        engagement = MentorshipEngagement.objects.create(
            mentorship=mentorship,
            student=student,
            alumnus= alumnus,
            source= MentorshipEngagement.Source.OFFER,
            source_id= offer.id,
        )
        
        offer.accept()
        mentorship.decrement_remaining_slots()
        return Response({"detail": "Offer accepted successfully.", "engagement_id": engagement.id},status=status.HTTP_201_CREATED)
    
@extend_schema(tags=['Mentorship Offers'], summary='Reject a mentorship offer (student)')
class RejectOfferView(OfferValidationMixin, APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        offer = self.get_offer()
        
        if offer.student != request.user.student_profile:
            return Response({"detail": "You are not authorized to reject this offer."}, status=status.HTTP_403_FORBIDDEN)
        
        offer.reject()
        
        return Response({"detail": "Offer rejected successfully."},status=status.HTTP_200_OK)
    
@extend_schema(tags=['Mentorship Offers'], summary='Withdraw a mentorship offer (alumnus)')
class WithdrawOfferView(OfferValidationMixin,APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        offer = self.get_offer()
        
        if offer.mentorship.alumnus != request.user.alumni_profile:
            return Response({"detail": "You are not authorized to withdraw this offer."}, status=status.HTTP_403_FORBIDDEN)
        
        offer.withdraw()
        
        return Response({"detail": "Offer withdrawn successfully."},status=status.HTTP_200_OK)
    
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
            return MentorshipApplication.objects.filter(mentorship__alumnus=user.alumni_profile).select_related('mentorship', 'student', 'mentorship__alumnus')
        
        elif user.role == User.Role.STUDENT:
            return MentorshipApplication.objects.filter(student=user.student_profile).select_related('mentorship', 'student')
        
        return MentorshipApplication.objects.none()
        
@extend_schema(tags=['Mentorship Applications'], summary='Retrieve a mentorship application by id (alumnus and student)')
class RetrieveMentorshipApplicationView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipApplicationSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return MentorshipApplication.objects.filter(mentorship__alumnus=user.alumni_profile).select_related('mentorship', 'student', 'mentorship__alumnus')
        
        elif user.role == User.Role.STUDENT:
            return MentorshipApplication.objects.filter(student=user.student_profile).select_related('mentorship', 'student')
        
        return MentorshipApplication.objects.none()
    
@extend_schema(tags=['Mentorship Applications'], summary='Accept a mentorship application (alumnus)')
class AcceptApplicationView(ApplicationValidationMixin, APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        application = self.get_application()
        
        mentorship = application.mentorship
        student = application.student
        alumnus = mentorship.alumnus
        
        if alumnus != request.user.alumni_profile:
            return Response({"detail": "You are not authorized to accept this application."}, status=status.HTTP_403_FORBIDDEN)
        
        if MentorshipEngagement.objects.filter(mentorship=mentorship, student=student).exists():
            return Response({"detail": "This student is already engaged in this mentorship."}, status=status.HTTP_400_BAD_REQUEST)
        
        engagement = MentorshipEngagement.objects.create(
            mentorship=mentorship,
            student=student,
            alumnus= alumnus,
            source=MentorshipEngagement.Source.APPLICATION,
            source_id=application.id,
        )
        
        application.accept()
        mentorship.decrement_remaining_slots()
        return Response({"detail": "Application accepted successfully.", "engagement_id": engagement.id},status=status.HTTP_201_CREATED)
    
@extend_schema(tags=['Mentorship Applications'], summary='Reject a mentorship application (alumnus)')
class RejectApplicationView(ApplicationValidationMixin, APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        application = self.get_application()
        
        mentorship = application.mentorship
        
        if mentorship.alumnus != request.user.alumni_profile:
            return Response({"detail": "You are not authorized to reject this application."}, status=status.HTTP_403_FORBIDDEN)
        
        application.reject()
        
        return Response({"detail": "Application rejected successfully."},status=status.HTTP_200_OK)
    
@extend_schema(tags=['Mentorship Applications'], summary='Withdraw a mentorship application (student)')
class WithdrawApplicationView(ApplicationValidationMixin, APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        application = self.get_application()
        
        if application.student != request.user.student_profile:
            return Response({"detail": "You are not authorized to withdraw this application."}, status=status.HTTP_403_FORBIDDEN)
        
        application.withdraw()
        
        return Response({"detail": "Application withdrawn successfully."},status=status.HTTP_200_OK)
    
@extend_schema(tags=['Mentorship Engagements'], summary='List all mentorship engagements (alumnus and student)')
class ListMentorshipEngagementsView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipEngagementSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return MentorshipEngagement.objects.filter(alumnus=user.alumni_profile).select_related('mentorship', 'student', 'alumnus')
        
        elif user.role == User.Role.STUDENT:
            return MentorshipEngagement.objects.filter(student=user.student_profile).select_related('mentorship', 'student')
        
        return MentorshipEngagement.objects.none()
    
@extend_schema(tags=['Mentorship Engagements'], summary='Retrieve a mentorship engagement by id (alumnus and student)')
class RetrieveMentorshipEngagementView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipEngagementSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return MentorshipEngagement.objects.filter(alumnus=user.alumni_profile).select_related('mentorship', 'student', 'alumnus')
        
        elif user.role == User.Role.STUDENT:
            return MentorshipEngagement.objects.filter(student=user.student_profile).select_related('mentorship', 'student')
        
        return MentorshipEngagement.objects.none()