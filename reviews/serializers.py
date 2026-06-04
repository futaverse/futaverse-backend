from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from engagements.models import BaseEngagement
from futaverse.lib import MODELS
from reviews.models import Review
from core.serializers import StudentInfoSerializer, AlumniInfoSerializer
from core.models import User

from .plugins import ENGAGEMENT_REVIEW_PLUGIN, ReviewType

class ReviewActorDetailSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ["email", "role", "profile"]
    
    def get_profile(self, obj):
        profile = obj.profile
        if profile is None:
            return None
        
        if obj.role == User.Role.STUDENT:
            return StudentInfoSerializer(profile).data
        elif obj.role == User.Role.ALUMNI:
            return AlumniInfoSerializer(profile).data
        
        return None


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_info = ReviewActorDetailSerializer(source="reviewer", read_only=True)
    reviewee_info = ReviewActorDetailSerializer(source="reviewee", read_only=True)

    class Meta:
        model = Review
        fields = [
            "sqid",
            "reviewer_info",
            "reviewee_info",
            "overall_rating",
            "review_text",
            "metrics",
            "editable_until",
            "created_at",
            "updated_at"
        ]
        read_only_fields = fields      
        
class CreateReviewSerializer(serializers.Serializer):
    engagement_type = serializers.ChoiceField(choices=['internship_engagement', 'mentorship_engagement'], required=True)
    engagement = serializers.SlugField(required=True)
    
    metrics = serializers.JSONField(required=False, default=dict)
    review_text = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        reviewer = self.context["request"].user
        validated_data = super().validate(attrs)
        
        engagement_type = validated_data.pop('engagement_type')
        engagement_id = validated_data.pop('engagement')
        metrics = validated_data.get("metrics", {})
        
        engagement_model = MODELS.get(engagement_type)

        engagement = get_object_or_404(engagement_model, sqid=engagement_id)
        
        if engagement.status != BaseEngagement.EngagementStatus.ACKNOWLEDGED:
            raise ValidationError("Engagement has not been acknowledged by one or both parties.")

        content_type = ContentType.objects.get_for_model(engagement_model)
        
        if reviewer == engagement.student.user:
            reviewee = engagement.alumnus.user
            review_type = ReviewType.STUDENT_RATES_ALUMNUS

        elif reviewer == engagement.alumnus.user:
            reviewee = engagement.student.user
            review_type = ReviewType.ALUMNUS_RATES_STUDENT
            
        else:
            raise ValidationError({"detail": "You are not part of this engagement."})
        
        if reviewee == reviewer:
            raise serializers.ValidationError("You cannot review yourself.")
            
        plugin = ENGAGEMENT_REVIEW_PLUGIN.get(review_type)
        
        metrics_serializer = plugin.metrics_serializer(data=metrics)
        metrics_serializer.is_valid(raise_exception=True)
        
        validated_metrics = metrics_serializer.validated_data

        validated_data["metrics"] = validated_metrics
        validated_data["overall_rating"] = plugin.compute_overall(validated_metrics)
        
        existing_review = Review.objects.filter(
            reviewer=reviewer,
            reviewee=reviewee,
            source_content_type=content_type,
            source_object_id=engagement.id
        ).exists()
        
        if existing_review:
            raise ValidationError({"detail": "You have already reviewed this engagement."})
        
        validated_data["reviewer"] = reviewer
        validated_data["reviewee"] = reviewee
        validated_data["engagement"] = engagement
        
        return validated_data

# class UpdateReviewSerializer(serializers.Serializer):
#     """Serializer for updating reviews."""
#     metrics = serializers.JSONField(required=False)
#     review_text = serializers.CharField(required=False, allow_blank=True)
    
#     def update(self, instance, validated_data):
#         metrics = validated_data.get("metrics")
#         review_text = validated_data.get("review_text")
        
#         return update_review(
#             review=instance,
#             metrics=metrics,
#             review_text=review_text
#         )
