from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from engagements.models import BaseEngagement

from .models import Post
from engagements.plugins import get_engagement_plugin

from futaverse.lib import MODELS

class ShareEngagementSerializer(serializers.Serializer):
    engagement_type = serializers.ChoiceField(choices=['internship_engagement', 'mentorship_engagement'], required=True)
    engagement = serializers.SlugField(required=True)
    content = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate(self, attrs):
        user = self.context['request'].user
        validated_data = super().validate(attrs)

        engagement_type = validated_data['engagement_type']
        engagement_id = validated_data['engagement']

        engagement_model = MODELS.get(engagement_type)

        engagement = get_object_or_404(
            engagement_model,
            sqid=engagement_id,
            student=user.student_profile
        )

        content_type = ContentType.objects.get_for_model(
            engagement_model
        )

        existing_post = Post.objects.filter(
            author=user,
            content_type=content_type,
            object_id=engagement.id,
            post_type=Post.PostType.ENGAGEMENT_STARTED
        ).exists()

        if existing_post:
            raise ValidationError({"detail": "You have already shared this engagement."})

        validated_data["engagement"] = engagement

        return validated_data
    
class PostSerializer(serializers.ModelSerializer):
    related_data = serializers.SerializerMethodField()
    class Meta:
        model = Post
        fields = ['post_type', 'content', 'is_public', 'sqid', 'created_at', 'related_data']
        
    def get_related_data(self, obj):
        related = obj.related_object
        
        plugin = get_engagement_plugin(related.__class__)

        if not plugin:
            return None

        serializer_class = plugin["serializer"]

        return serializer_class(related).data
    
class ShareEngagementCompletionSerializer(serializers.Serializer):
    engagement_type = serializers.ChoiceField(choices=['internship_engagement', 'mentorship_engagement'], required=True)
    engagement = serializers.SlugField(required=True)
    content = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate(self, attrs):
        user = self.context['request'].user

        engagement_type = attrs['engagement_type']
        engagement_id = attrs['engagement']

        engagement_model = MODELS.get(engagement_type)

        engagement = get_object_or_404(
            engagement_model,
            sqid=engagement_id,
            student=user.student_profile
        )
        
        if engagement.status != BaseEngagement.EngagementStatus.ACKNOWLEDGED:
            raise ValidationError("Engagement has not been acknowledged by one or both parties.")

        content_type = ContentType.objects.get_for_model(engagement_model)

        existing_post = Post.objects.filter(
            author=user,
            content_type=content_type,
            object_id=engagement.id,
            post_type=Post.PostType.ENGAGEMENT_COMPLETED
        ).exists()

        if existing_post:
            raise ValidationError({"detail": "You have already shared this engagement completion."})

        attrs["engagement"] = engagement

        return attrs