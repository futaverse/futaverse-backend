from drf_spectacular.utils import extend_schema

from rest_framework import generics

from internships.models import InternshipOffer
from internships.serializers import (
    InternshipOfferSerializer,
    StudentManageInternshipOfferSerializer,
    AlumnusManageInternshipOfferSerializer,
    InternshipEngagementSerializer,
)
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

from engagements.models import Engagement
from engagements.helpers import queryset_by_role
from engagements.views import AcceptOfferView, RejectOfferView, WithdrawOfferView


@extend_schema(tags=['Internship Offers'], summary='Create an internship offer (alumnus)')
class CreateInternshipOfferView(generics.CreateAPIView):
    serializer_class = InternshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus]


@extend_schema(tags=['Internship Offers'], summary='List internship offers (alumnus, student)')
class ListInternshipOfferView(generics.ListAPIView):
    serializer_class = InternshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            InternshipOffer,
            alumnus_filter=lambda: {
                "internship__alumnus": self.request.user.alumni_profile,
                "status": "pending",
            },
            student_filter=lambda: {
                "student": self.request.user.student_profile,
                "status": "pending",
            },
            select_related=("internship", "student"),
            order_by="-created_at",
        )


@extend_schema(tags=['Internship Offers'], summary='Retrieve an internship offer by id (alumnus and student)')
class RetrieveInternshipOfferView(generics.RetrieveAPIView):
    serializer_class = InternshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    lookup_field = 'sqid'

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            InternshipOffer,
            alumnus_filter=lambda: {"internship__alumnus": self.request.user.alumni_profile},
            student_filter=lambda: {"student": self.request.user.student_profile},
            select_related=("internship", "student", "internship__alumnus"),
        )


@extend_schema(tags=['Internship Offers'], summary='Accept an internship offer (student)')
class AcceptInternshipOfferView(AcceptOfferView):
    engagement_type = Engagement.EngagementType.INTERNSHIP
    engagement_serializer_class = InternshipEngagementSerializer
    validation_serializer_class = StudentManageInternshipOfferSerializer
    relation_name = "internship"


@extend_schema(tags=['Internship Offers'], summary='Reject an internship offer (student)')
class RejectInternshipOfferView(RejectOfferView):
    validation_serializer_class = StudentManageInternshipOfferSerializer


@extend_schema(tags=['Internship Offers'], summary='Withdraw an internship offer (alumnus)')
class WithdrawInternshipOfferView(WithdrawOfferView):
    validation_serializer_class = AlumnusManageInternshipOfferSerializer
