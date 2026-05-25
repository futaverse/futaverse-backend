from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Post
from .lib import POST_RELATED_SERIALIZERS

from futaverse.lib import MODELS

class ShareEngagementSerializer(serializers.Serializer):
    engagement_type = serializers.ChoiceField(choices=['internship_engagement', 'mentorship_engagement'], required=True)
    engagement_id = serializers.SlugField(required=True)
    content = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)

        engagement_type = validated_data['engagement_type']
        engagement_id = validated_data['engagement_id']

        user = self.context['request'].user

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
            raise ValidationError("You have already shared this engagement.")

        validated_data["engagement"] = engagement

        return validated_data
    
class PostSerializer(serializers.ModelSerializer):
    related_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['post_type', 'content', 'is_public', 'sqid', 'created_at', 'related_data']
        
    def get_related_data(self, obj):
        related = obj.related_object
        
        serializer_class = POST_RELATED_SERIALIZERS.get(related.__class__)

        if not serializer_class:
            return None

        return serializer_class(related).data