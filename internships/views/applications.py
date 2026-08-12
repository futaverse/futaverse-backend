from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from internships.models import InternshipApplication, InternshipEngagement
from internships.serializers import (
    InternshipApplicationSerializer,
    StudentManageInternshipApplicationSerializer,
    AlumnusManageInternshipApplicationSerializer,
    InternshipEngagementSerializer,
)
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

from engagements.helpers import queryset_by_role
from engagements.views import AcceptApplicationView, RejectApplicationView, WithdrawApplicationView


@extend_schema(tags=['Internship Applications'], summary='Apply for an internship (student)')
class CreateInternshipApplicationView(generics.CreateAPIView):
    serializer_class = InternshipApplicationSerializer
    permission_classes = [IsAuthenticatedStudent]

    @transaction.atomic
    def perform_create(self, serializer):
        student = self.request.user.student_profile
        serializer.save(student=student)


@extend_schema(tags=['Internship Applications'], summary='List all internship applications (alumnus and student)')
class ListInternshipApplicationsView(generics.ListAPIView):
    serializer_class = InternshipApplicationSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            InternshipApplication,
            alumnus_filter=lambda: {
                "internship__alumnus": self.request.user.alumni_profile,
                "status": "pending",
            },
            student_filter=lambda: {
                "student": self.request.user.student_profile,
                "status": "pending",
            },
            select_related=("internship", "student", "resume"),
            order_by="-created_at",
        )


@extend_schema(tags=['Internship Applications'], summary='Retrieve an internship application by id (alumnus and student)')
class RetrieveInternshipApplicationView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = InternshipApplicationSerializer
    lookup_field = 'sqid'

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            InternshipApplication,
            alumnus_filter=lambda: {"internship__alumnus": self.request.user.alumni_profile},
            student_filter=lambda: {"student": self.request.user.student_profile},
            select_related=("internship", "student", "internship__alumnus"),
        )


@extend_schema(tags=['Internship Applications'], summary='Accept an internship application (alumnus)')
class AcceptInternshipApplicationView(AcceptApplicationView):
    application_model = InternshipApplication
    engagement_model = InternshipEngagement
    engagement_serializer_class = InternshipEngagementSerializer
    validation_serializer_class = AlumnusManageInternshipApplicationSerializer
    relation_name = "internship"


@extend_schema(tags=['Internship Applications'], summary='Reject an internship application (alumnus)')
class RejectInternshipApplicationView(RejectApplicationView):
    validation_serializer_class = AlumnusManageInternshipApplicationSerializer


@extend_schema(tags=['Internship Applications'], summary='Withdraw an internship application (student)')
class WithdrawInternshipApplicationView(WithdrawApplicationView):
    validation_serializer_class = StudentManageInternshipApplicationSerializer
