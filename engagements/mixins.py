from django_q.tasks import async_task
from django.db import transaction

from rest_framework import generics
from rest_framework.exceptions import ValidationError
from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

from .tasks import schedule_auto_ackowledgement_task
from .models import BaseEngagement
class MarkEngagementCompletedMixin:
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None
    http_method_names = ['patch']
    lookup_field = 'sqid'
    engagement_type = None
    
    def perform_update(self, serializer):
        engagement = self.get_object()
        
        if engagement.status != BaseEngagement.EngagementStatus.ACTIVE:
            raise ValidationError("Only active engagements can be completed.")
        
        with transaction.atomic():
            engagement.update_status(BaseEngagement.EngagementStatus.COMPLETED)
            
        engagement_data = {
            'engagement_type': self.engagement_type,
            'sqid': engagement.sqid
        }

        # TODO: FE dev urges student to acknowledge completion. It will be auto-ackowledged in 48 hours.
        transaction.on_commit(lambda: async_task(
            schedule_auto_ackowledgement_task,
            engagement_data
        ))
        
class MarkEngagementAcknowledgedMixin:
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None
    http_method_names = ['patch']
    lookup_field = 'sqid'
    engagement_type = None
    
    def perform_update(self, serializer):
        engagement = self.get_object()
        
        if engagement.status != BaseEngagement.EngagementStatus.COMPLETED:
            raise ValidationError("Only completed engagements can be acknowledged.")
        
        engagement.update_status(BaseEngagement.EngagementStatus.ACKNOWLEDGED)