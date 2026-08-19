from django.db import transaction
from django_q.tasks import async_task
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import OR, IsAuthenticated

from engagements.helpers import queryset_by_role
from engagements.mixins import (
    MarkEngagementAcknowledgedMixin,
    MarkEngagementCompletedMixin,
)
from engagements.models import Engagement
from feed.models import FeedEvent
from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent
from mentorships.models import FocusArea, Mentorship, MentorshipCategory
from mentorships.serializers import (
    MentorshipEngagementSerializer,
    MentorshipSerializer,
    MentorshipStatusSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="List mentorships (alumnus)"),
    create=extend_schema(summary="Create an mentorship (alumnus)"),
)
@extend_schema(tags=["Mentorships"])
class ListCreateMentorshipView(generics.ListCreateAPIView):
    serializer_class = MentorshipSerializer
    permission_classes = [IsAuthenticatedAlumnus]

    def get_queryset(self):
        user = self.request.user
        return Mentorship.objects.filter(alumnus=user.alumni_profile).select_related(
            "alumnus"
        )

    def perform_create(self, serializer):
        alumnus = self.request.user.alumni_profile
        mentorship = serializer.save(alumnus=alumnus)

        transaction.on_commit(
            lambda: async_task(
                "feed.tasks.create_feed_event_task",
                event_type=FeedEvent.EventType.MENTORSHIP_CREATED,
                related_object_id=mentorship.id,
                related_model="mentorship",
                audience=FeedEvent.Audience.PUBLIC,
                data={
                    "title": mentorship.title,
                    "alumni": mentorship.alumnus.full_name,
                    "category": mentorship.category,
                    "available_slots": mentorship.available_slots,
                    "remaining_slots": mentorship.remaining_slots,
                    "created_at": mentorship.created_at.isoformat(),
                },
            )
        )


@extend_schema_view(
    retrieve=extend_schema(summary="Get an mentorship by id (alumnus)"),
    update=extend_schema(summary="Update an mentorship by id (alumnus)"),
    destroy=extend_schema(summary="Delete an mentorship by id (alumnus)"),
)
@extend_schema(
    tags=["Mentorships"],
    summary="Retrieve (GET), update (PATCH) and delete (DELETE) a mentorship by id (alumnus)",
)
class RetrieveUpdateDestroyMentorshipView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MentorshipSerializer
    permission_classes = [IsAuthenticatedAlumnus]
    http_method_names = ["get", "patch", "delete"]
    lookup_field = "sqid"

    def get_permissions(self):
        if self.request.method == "GET":
            return [OR(IsAuthenticatedAlumnus(), IsAuthenticatedStudent())]
        return [IsAuthenticatedAlumnus()]

    def get_queryset(self):
        user = self.request.user
        return Mentorship.objects.filter(alumnus=user.alumni_profile).select_related(
            "alumnus"
        )

    def perform_destroy(self, instance):
        instance.soft_delete()


@extend_schema(
    tags=["Mentorships"], summary="Toggle active status of a mentorship (alumnus)"
)
class ToggleMentorshipActiveView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = MentorshipStatusSerializer
    http_method_names = ["patch"]
    lookup_field = "sqid"

    def get_queryset(self):
        return Mentorship.objects.filter(alumnus=self.request.user.alumni_profile)

    def perform_update(self, serializer):
        serializer.instance.toggle_active()


@extend_schema(
    tags=["Mentorship Engagements"],
    summary="List all mentorship engagements (alumnus and student)",
)
class ListMentorshipEngagementsView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipEngagementSerializer

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            Engagement,
            alumnus_filter=lambda: {
                "engagement_type": Engagement.EngagementType.MENTORSHIP,
                "alumnus": self.request.user.alumni_profile,
            },
            student_filter=lambda: {
                "engagement_type": Engagement.EngagementType.MENTORSHIP,
                "student": self.request.user.student_profile,
            },
            select_related=(
                "student",
                "alumnus",
                "mentorship_detail__mentorship",
                "mentorship_detail__application",
                "mentorship_detail__offer",
            ),
        )


@extend_schema(
    tags=["Mentorship Engagements"],
    summary="Retrieve a mentorship engagement by id (any authenticated user)",
)
class RetrieveMentorshipEngagementView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MentorshipEngagementSerializer
    lookup_field = "sqid"

    def get_queryset(self):
        return Engagement.objects.filter(
            engagement_type=Engagement.EngagementType.MENTORSHIP
        ).select_related(
            "student",
            "alumnus",
            "mentorship_detail__mentorship",
            "mentorship_detail__application",
            "mentorship_detail__offer",
        )


@extend_schema(
    tags=["Mentorships"],
    summary="List mentorship categories and focus areas (alumnus and student)",
)
class MentorshipChoicesView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]

    def get(self, request):
        return Response(
            {
                "categories": [
                    {"value": v, "label": l} for v, l in MentorshipCategory.choices
                ],
                "focus_areas": [{"value": v, "label": l} for v, l in FocusArea.choices],
            }
        )


@extend_schema(
    tags=["Mentorship Engagements"],
    summary="Mark a mentorship engagement as completed (alumnus)",
)
class MarkMentorshipCompletedView(MarkEngagementCompletedMixin, generics.UpdateAPIView):
    queryset = Engagement.objects.all()
    engagement_type = Engagement.EngagementType.MENTORSHIP
    serializer_class = MentorshipEngagementSerializer


@extend_schema(
    tags=["Mentorship Engagements"],
    summary="Mark a mentorship engagement as acknowledged (student)",
)
class MarkMentorshipAcknowledgedView(
    MarkEngagementAcknowledgedMixin, generics.UpdateAPIView
):
    queryset = Engagement.objects.all()
    engagement_type = Engagement.EngagementType.MENTORSHIP
    serializer_class = MentorshipEngagementSerializer
