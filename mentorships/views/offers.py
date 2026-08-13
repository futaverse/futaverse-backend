from drf_spectacular.utils import extend_schema

from rest_framework import generics

from mentorships.models import MentorshipOffer
from mentorships.serializers import (
    MentorshipEngagementSerializer,
    MentorshipOfferSerializer,
    StudentManageMentorshipOfferSerializer,
    AlumnusManageMentorshipOfferSerializer,
)
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

from engagements.helpers import queryset_by_role
from engagements.models import Engagement
from engagements.views import AcceptOfferView, RejectOfferView, WithdrawOfferView


@extend_schema(tags=['Mentorship Offers'], summary='Create a mentorship offer (alumnus)')
class CreateMentorshipOfferView(generics.CreateAPIView):
    serializer_class = MentorshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus]


@extend_schema(tags=['Mentorship Offers'], summary='List mentorship offers (alumnus, student)')
class ListMentorshipOfferView(generics.ListAPIView):
    serializer_class = MentorshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            MentorshipOffer,
            alumnus_filter=lambda: {
                "mentorship__alumnus": self.request.user.alumni_profile,
                "status": "pending",
            },
            student_filter=lambda: {
                "student": self.request.user.student_profile,
                "status": "pending",
            },
            select_related=("mentorship", "student"),
            order_by="-created_at",
        )


@extend_schema(tags=['Mentorship Offers'], summary='Retrieve a mentorship offer by id (alumnus and student)')
class RetrieveMentorshipOfferView(generics.RetrieveAPIView):
    serializer_class = MentorshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    lookup_field = 'sqid'

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            MentorshipOffer,
            alumnus_filter=lambda: {"mentorship__alumnus": self.request.user.alumni_profile},
            student_filter=lambda: {"student": self.request.user.student_profile},
            select_related=("mentorship", "student", "mentorship__alumnus"),
        )


@extend_schema(tags=['Mentorship Offers'], summary='Accept a mentorship offer (student)')
class AcceptMentorshipOfferView(AcceptOfferView):
    offer_model = MentorshipOffer
    engagement_type = Engagement.EngagementType.MENTORSHIP
    engagement_serializer_class = MentorshipEngagementSerializer
    validation_serializer_class = StudentManageMentorshipOfferSerializer
    relation_name = "mentorship"


@extend_schema(tags=['Mentorship Offers'], summary='Reject a mentorship offer (student)')
class RejectMentorshipOfferView(RejectOfferView):
    validation_serializer_class = StudentManageMentorshipOfferSerializer


@extend_schema(tags=['Mentorship Offers'], summary='Withdraw a mentorship offer (alumnus)')
class WithdrawMentorshipOfferView(WithdrawOfferView):
    validation_serializer_class = AlumnusManageMentorshipOfferSerializer
