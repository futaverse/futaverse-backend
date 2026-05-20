from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from mentorships.models import MentorshipOffer, MentorshipEngagement, MentorshipStatus
from mentorships.serializers import MentorshipOfferSerializer, ManageMentorshipOfferSerializer
from mentorships.mixins import OfferValidationMixin
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

@extend_schema(tags=['Mentorship Offers'], summary='Create a mentorship offer (alumnus)')
class CreateMentorshipOfferView(generics.CreateAPIView):
    serializer_class = MentorshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus]
    
    # TODO: Send notification to student when an offer is created 
    
@extend_schema(tags=['Mentorship Offers'], summary='List mentorship offers (alumnus, student)')
class ListMentorshipOfferView(generics.ListAPIView):
    serializer_class = MentorshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return MentorshipOffer.objects.filter(mentorship__alumnus=user.alumni_profile, status=MentorshipStatus.PENDING).select_related('mentorship', 'student').order_by('-created_at')
        
        elif user.role == User.Role.STUDENT:
            return MentorshipOffer.objects.filter(student=user.student_profile, status=MentorshipStatus.PENDING).select_related('mentorship', 'student').order_by('-created_at')
        
        return MentorshipOffer.objects.none()
        
@extend_schema(tags=['Mentorship Offers'], summary='Retrieve a mentorship offer by id (alumnus and student)')
class RetrieveMentorshipOfferView(generics.RetrieveAPIView):
    serializer_class = MentorshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    lookup_field = 'sqid'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return MentorshipOffer.objects.filter(mentorship__alumnus=user.alumni_profile).select_related('mentorship', 'student', 'mentorship__alumnus')
        
        elif user.role == User.Role.STUDENT:
            return MentorshipOffer.objects.filter(student=user.student_profile).select_related('mentorship', 'student')
        
        return MentorshipOffer.objects.none()
        
@extend_schema(tags=['Mentorship Offers'], summary='Accept a mentorship offer (student)')
class AcceptMentorshipOfferView(OfferValidationMixin, APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = ManageMentorshipOfferSerializer(
            data={"offer_id": kwargs.get("offer_id")},
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        offer = serializer.validated_data["offer"]
        
        mentorship = offer.mentorship
        student = offer.student
        alumnus = mentorship.alumnus
        
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
class RejectMentorshipOfferView(OfferValidationMixin, APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        serializer = ManageMentorshipOfferSerializer(
            data={"offer_id": kwargs.get("offer_id")},
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        offer = serializer.validated_data["offer"]
        
        offer.reject()
        
        return Response({"detail": "Offer rejected successfully."},status=status.HTTP_200_OK)
    
@extend_schema(tags=['Mentorship Offers'], summary='Withdraw a mentorship offer (alumnus)')
class WithdrawMentorshipOfferView(OfferValidationMixin,APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        serializer = ManageMentorshipOfferSerializer(
            data={"offer_id": kwargs.get("offer_id")},
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        offer = serializer.validated_data["offer"]
        
        offer.withdraw()
        
        return Response({"detail": "Offer withdrawn successfully."},status=status.HTTP_200_OK)