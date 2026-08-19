from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import FeedEvent
from .serializers import FeedCursorPagination, FeedEventSerializer


@extend_schema(tags=["Feed"], summary="Get feed for user (student, alumnus)")
class FeedView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = FeedCursorPagination
    serializer_class = FeedEventSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = FeedEvent.objects.filter(
            is_active=True, audience__in=[user.role, FeedEvent.Audience.PUBLIC]
        )
        return queryset.order_by("-score", "-created_at", "id")

    # def list(self, request, *args, **kwargs):
    #     response = super().list(request, *args, **kwargs)
    #
    #     print(response.data)
    #
    #     ids = [item['sqid'] for item in response.data['results']]
    #     if ids:
    #         record_impressions_task.delay(request.user.id, ids)
    #
    #     return response

    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     page = self.paginate_queryset(queryset)

    #     ids = [event.id for event in page]
    #     if ids:
    #         async_task("feed.tasks.record_impressions_task", request.user.id, ids)

    #     serializer = self.get_serializer(page, many=True)
    #     return self.get_paginated_response(serializer.data)
