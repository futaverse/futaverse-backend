from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from internships.models import InternshipOffer, InternshipEngagement, InternshipStatus
from internships.serializers import InternshipOfferSerializer, ManageInternshipOfferSerializer, InternshipEngagementSerializer
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

@extend_schema(tags=['Internship Offers'], summary='Create an internship offer (alumnus)')
class CreateInternshipOfferView(generics.CreateAPIView):
    serializer_class = InternshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus]
    
    # TODO: Send notification to student when an offer is created 
    
@extend_schema(tags=['Internship Offers'], summary='List internship offers (alumnus, student)')
class ListInternshipOfferView(generics.ListAPIView):
    serializer_class = InternshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    
    def get_queryset(self):
        user = self.request.user
        print(user)
        
        if user.role == User.Role.ALUMNI:
            return InternshipOffer.objects.filter(internship__alumnus=user.alumni_profile, status=InternshipStatus.PENDING).select_related('internship', 'student',).order_by('-created_at')
        
        elif user.role == User.Role.STUDENT:
            return InternshipOffer.objects.filter(student=user.student_profile, status=InternshipStatus.PENDING).select_related('internship', 'student').order_by('-created_at')
        
        return InternshipOffer.objects.none()
    
@extend_schema(tags=['Internship Offers'], summary='Retrieve an internship offer by id (alumnus and student)')
class RetrieveInternshipOfferView(generics.RetrieveAPIView):
    serializer_class = InternshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    lookup_field = 'sqid'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return InternshipOffer.objects.filter(internship__alumnus=user.alumni_profile).select_related('internship', 'student', 'internship__alumnus')
        
        elif user.role == User.Role.STUDENT:
            return InternshipOffer.objects.filter(student=user.student_profile).select_related('internship', 'student')
        
        return InternshipOffer.objects.none()
    
@extend_schema(tags=['Internship Offers'], summary='Accept an internship offer (student)')
class AcceptInternshipOfferView(APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = ManageInternshipOfferSerializer(
            data={"offer_id": kwargs.get("offer_id")},
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        offer = serializer.validated_data["offer"]
        
        internship = offer.internship
        student = offer.student
        alumnus = internship.alumnus
        
        engagement = InternshipEngagement.objects.create(
            internship=internship,
            student=student,
            alumnus= alumnus,
            source= InternshipEngagement.Source.OFFER,
            source_id= offer.id,
        )
        
        offer.accept()
        internship.decrement_remaining_slots()
        return Response({"detail": "Offer accepted successfully.", "engagement": InternshipEngagementSerializer(engagement).data},status=status.HTTP_201_CREATED)
    
@extend_schema(tags=['Internship Offers'], summary='Reject an internship offer (student)')
class RejectInternshipOfferView(APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        serializer = ManageInternshipOfferSerializer(
            data={"offer_id": kwargs.get("offer_id")},
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        offer = serializer.validated_data["offer"]
        
        offer.reject()
        
        return Response({"detail": "Application rejected successfully."}, status=status.HTTP_200_OK)
    
@extend_schema(tags=['Internship Offers'], summary='Withdraw an internship offer (alumnus)')
class WithdrawInternshipOfferView(APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    
    def post(self, request, *args, **kwargs):
        serializer = ManageInternshipOfferSerializer(
            data={"offer_id": kwargs.get("offer_id")},
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        offer = serializer.validated_data["offer"]
        
        offer.withdraw()
        
        return Response({"detail": "Offer withdrawn successfully."},status=status.HTTP_200_OK)