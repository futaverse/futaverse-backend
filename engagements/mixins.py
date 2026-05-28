from django_q.tasks import async_task
from django.db import transaction

from rest_framework import generics
from futaverse.permissions import IsAuthenticatedAlumnus

from notifications.tasks import send_notifications_task

class MarkEngagementCompletedMixin:
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    http_method_names = ['patch']
    lookup_field = 'sqid'
    engagement_type = None
    
    def perform_update(self, serializer):
        with transaction.atomic():
            engagement = self.get_object()
            engagement.mark_as_completed()

        transaction.on_commit(lambda: async_task(
            send_notifications_task,
            user_ids=[engagement.student.user.id],
            title=f'{self.engagement_type} Completed',
            content=f'Your {self.engagement_type.lower()} with {engagement.alumnus.full_name} has been marked as completed.'
        ))