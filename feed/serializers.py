from rest_framework import serializers
from rest_framework.pagination import CursorPagination

from .models import FeedEvent


class FeedCursorPagination(CursorPagination):
    page_size = 20
    ordering = ("-score", "shuffle_seed", "id")


class FeedEventSerializer(serializers.ModelSerializer):
    score = serializers.IntegerField(read_only=True)

    class Meta:
        model = FeedEvent
        fields = ["sqid", "event_type", "data", "score", "created_at"]
