# views.py

import base64, json
from datetime import datetime

from django.db.models import Count, Value, IntegerField

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import FeedEvent
from .serializers import FeedCursorPagination, FeedEventSerializer
from .tasks import record_impressions_task


# def encode_cursor(created_at, event_id):
#     data = {'ts': created_at.isoformat(), 'id': event_id}
#     return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


# def decode_cursor(cursor):
#     data = json.loads(base64.urlsafe_b64decode(cursor))
#     return datetime.fromisoformat(data['ts']), data['id']

class FeedView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = FeedCursorPagination
    serializer_class = FeedEventSerializer
    
    def get_queryset(self):
        profile = self.request.user.profile
        
        match_filter = profile.feed_match_filter()
        queryset = FeedEvent.objects.filter(is_active=True).exclude(
            impressions__user=self.request.user
        )

        # Ranking based on number of matched filters
        if match_filter:
            queryset = queryset.annotate(score=Count('targets', filter=match_filter))
        else:
            queryset = queryset.annotate(score=Value(0, output_field=IntegerField()))  # score=0 for everyone

        return queryset.order_by('-score', '-created_at')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        ids = [item['id'] for item in response.data['results']]
        if ids:
            record_impressions_task.delay(request.user.id, ids)

        return response