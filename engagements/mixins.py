from django_q.tasks import async_task
from django.db import transaction
from django.core.cache import cache

from rest_framework.exceptions import ValidationError
from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent
from futaverse.exceptions import ConflictError

from .models import BaseEngagement


class MarkEngagementCompletedMixin:
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    http_method_names = ['patch']
    lookup_field = 'sqid'
    engagement_type = None

    def get_queryset(self):
        return self.queryset.filter(alumnus=self.request.user.alumni_profile)

    def perform_update(self, serializer):
        engagement = serializer.instance
        lock_key = f"engagement_status_{engagement.sqid}"

        if cache.get(lock_key):
            raise ConflictError({"detail": "Request already in progress."})

        cache.set(lock_key, True, timeout=10)

        if engagement.status != BaseEngagement.EngagementStatus.ACTIVE:
            raise ValidationError("Only active engagements can be completed.")

        with transaction.atomic():
            engagement.update_status(BaseEngagement.EngagementStatus.COMPLETED)

        engagement_data = {
            'engagement_type': self.engagement_type,
            'sqid': engagement.sqid
        }

        transaction.on_commit(lambda: async_task(
            "engagements.tasks.schedule_auto_acknowledgement_task",
            engagement_data
        ))


class MarkEngagementAcknowledgedMixin:
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    http_method_names = ['patch']
    lookup_field = 'sqid'
    engagement_type = None

    def get_queryset(self):
        return self.queryset.filter(student=self.request.user.student_profile)

    def perform_update(self, serializer):
        engagement = serializer.instance
        lock_key = f"engagement_status_{engagement.sqid}"

        if cache.get(lock_key):
            raise ConflictError({"detail": "Request already in progress."})

        cache.set(lock_key, True, timeout=10)

        if engagement.status != BaseEngagement.EngagementStatus.COMPLETED:
            raise ValidationError("Only completed engagements can be acknowledged.")

        engagement.update_status(BaseEngagement.EngagementStatus.ACKNOWLEDGED)