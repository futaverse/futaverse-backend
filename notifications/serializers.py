from rest_framework import serializers

from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Notification
        fields = ['sqid', 'title', 'content', 'is_read', 'created_at', 'read_at']
        read_only_fields = ['sqid', 'created_at', 'is_read', 'read_at']
    