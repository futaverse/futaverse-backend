from django.db import transaction
from django_q.tasks import async_task
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.permissions import OR, IsAuthenticated

from engagements.helpers import queryset_by_role
from engagements.mixins import (
    MarkEngagementAcknowledgedMixin,
    MarkEngagementCompletedMixin,
)
from engagements.models import Engagement
from feed.models import FeedEvent
from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent
from internships.models import Internship
from internships.serializers import (
    InternshipEngagementSerializer,
    InternshipSerializer,
    InternshipStatusSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="List internships (alumnus)"),
    create=extend_schema(summary="Create an internship (alumnus)"),
)
@extend_schema(tags=["Internships"])
class ListCreateInternshipView(generics.ListCreateAPIView):
    serializer_class = InternshipSerializer
    permission_classes = [IsAuthenticatedAlumnus]

    def get_queryset(self):
        user = self.request.user
        return (
            Internship.objects.filter(alumnus=user.alumni_profile)
            .select_related("alumnus")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        alumnus = self.request.user.alumni_profile
        internship = serializer.save(alumnus=alumnus)

        transaction.on_commit(
            lambda: async_task(
                "feed.tasks.create_feed_event_task",
                event_type=FeedEvent.EventType.INTERNSHIP_CREATED,
                related_object_id=internship.id,
                related_model="internship",
                audience=FeedEvent.Audience.STUDENT,
                data={
                    "title": internship.title,
                    "alumni": internship.alumnus.full_name,
                    "work_mode": internship.work_mode,
                    "engagement_type": internship.engagement_type,
                    "stipend": str(internship.stipend),
                    "is_paid": internship.is_paid,
                    "available_slots": internship.available_slots,
                    "remaining_slots": internship.remaining_slots,
                    "created_at": internship.created_at.isoformat(),
                },
            )
        )


@extend_schema_view(
    retrieve=extend_schema(summary="Get an internship by id (alumnus, student)"),
    update=extend_schema(summary="Update an internship by id (alumnus)"),
    destroy=extend_schema(summary="Delete an internship by id (alumnus)"),
)
@extend_schema(tags=["Internships"])
class InternshipDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InternshipSerializer
    http_method_names = ["get", "patch", "delete"]
    lookup_field = "sqid"

    def get_permissions(self):
        if self.request.method == "GET":
            return [OR(IsAuthenticatedAlumnus(), IsAuthenticatedStudent())]
        return [IsAuthenticatedAlumnus()]

    def get_queryset(self):
        if self.request.method == "GET":
            return Internship.objects.all()
        return Internship.objects.filter(alumnus=self.request.user.alumni_profile)

    def perform_destroy(self, instance):
        instance.soft_delete()


@extend_schema(
    tags=["Internships"], summary="Toggle internship active status (alumnus)"
)
class ToggleInternshipActiveView(generics.UpdateAPIView):
    serializer_class = InternshipStatusSerializer
    http_method_names = ["patch"]
    permission_classes = [IsAuthenticatedAlumnus]
    lookup_field = "sqid"

    def get_queryset(self):
        return Internship.objects.filter(alumnus=self.request.user.alumni_profile)

    def perform_update(self, serializer):
        serializer.instance.toggle_active()


@extend_schema(
    tags=["Internship Engagements"],
    summary="List all internship engagements (alumnus and student)",
)
class ListInternshipEngagementsView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = InternshipEngagementSerializer

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            Engagement,
            alumnus_filter=lambda: {
                "engagement_type": Engagement.EngagementType.INTERNSHIP,
                "alumnus": self.request.user.alumni_profile,
            },
            student_filter=lambda: {
                "engagement_type": Engagement.EngagementType.INTERNSHIP,
                "student": self.request.user.student_profile,
            },
            select_related=(
                "student",
                "alumnus",
                "internship_detail__internship",
                "internship_detail__application",
                "internship_detail__offer",
            ),
        )


@extend_schema(
    tags=["Internship Engagements"],
    summary="Retrieve an internship engagement by id (any authenticated user)",
)
class RetrieveInternshipEngagementView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InternshipEngagementSerializer
    lookup_field = "sqid"

    def get_queryset(self):
        return Engagement.objects.filter(
            engagement_type=Engagement.EngagementType.INTERNSHIP
        ).select_related(
            "student",
            "alumnus",
            "internship_detail__internship",
            "internship_detail__application",
            "internship_detail__offer",
        )


@extend_schema(
    tags=["Internship Engagements"],
    summary="Mark an internship engagement as completed (alumnus)",
)
class MarkInternshipCompletedView(MarkEngagementCompletedMixin, generics.UpdateAPIView):
    queryset = Engagement.objects.all()
    engagement_type = Engagement.EngagementType.INTERNSHIP
    serializer_class = InternshipEngagementSerializer


@extend_schema(
    tags=["Internship Engagements"],
    summary="Mark an internship engagement as acknowledged (student)",
)
class MarkInternshipAcknowledgedView(
    MarkEngagementAcknowledgedMixin, generics.UpdateAPIView
):
    queryset = Engagement.objects.all()
    engagement_type = Engagement.EngagementType.INTERNSHIP
    serializer_class = InternshipEngagementSerializer
