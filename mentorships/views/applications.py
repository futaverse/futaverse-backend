from drf_spectacular.utils import extend_schema
from rest_framework import generics

from engagements.helpers import queryset_by_role
from engagements.models import Engagement
from engagements.views import (
    AcceptApplicationView,
    RejectApplicationView,
    WithdrawApplicationView,
)
from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent
from mentorships.models import MentorshipApplication
from mentorships.serializers import (
    AlumnusManageMentorshipApplicationSerializer,
    MentorshipApplicationSerializer,
    MentorshipEngagementSerializer,
    StudentManageMentorshipApplicationSerializer,
)


@extend_schema(
    tags=["Mentorship Applications"], summary="Apply for a mentorship (student)"
)
class CreateMentorshipApplicationView(generics.CreateAPIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = MentorshipApplicationSerializer

    def perform_create(self, serializer):
        student = self.request.user.student_profile
        serializer.save(student=student)


@extend_schema(
    tags=["Mentorship Applications"],
    summary="List mentorship applications (alumnus and student)",
)
class ListMentorshipApplicationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipApplicationSerializer

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            MentorshipApplication,
            alumnus_filter=lambda: {
                "mentorship__alumnus": self.request.user.alumni_profile,
                "status": "pending",
            },
            student_filter=lambda: {
                "student": self.request.user.student_profile,
                "status": "pending",
            },
            select_related=("mentorship", "student", "mentorship__alumnus"),
            order_by="-created_at",
        )


@extend_schema(
    tags=["Mentorship Applications"],
    summary="Retrieve a mentorship application by id (alumnus and student)",
)
class RetrieveMentorshipApplicationView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipApplicationSerializer
    lookup_field = "sqid"

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            MentorshipApplication,
            alumnus_filter=lambda: {
                "mentorship__alumnus": self.request.user.alumni_profile
            },
            student_filter=lambda: {"student": self.request.user.student_profile},
            select_related=("mentorship", "student", "mentorship__alumnus"),
        )


@extend_schema(
    tags=["Mentorship Applications"],
    summary="Accept a mentorship application (alumnus)",
)
class AcceptMentorshipApplicationView(AcceptApplicationView):
    engagement_type = Engagement.EngagementType.MENTORSHIP
    engagement_serializer_class = MentorshipEngagementSerializer
    validation_serializer_class = AlumnusManageMentorshipApplicationSerializer
    relation_name = "mentorship"


@extend_schema(
    tags=["Mentorship Applications"],
    summary="Reject a mentorship application (alumnus)",
)
class RejectMentorshipApplicationView(RejectApplicationView):
    validation_serializer_class = AlumnusManageMentorshipApplicationSerializer


@extend_schema(
    tags=["Mentorship Applications"],
    summary="Withdraw a mentorship application (student)",
)
class WithdrawMentorshipApplicationView(WithdrawApplicationView):
    validation_serializer_class = StudentManageMentorshipApplicationSerializer
