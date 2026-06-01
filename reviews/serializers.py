from rest_framework import serializers

from reviews.models import Review
from reviews.services import create_review, update_review
from core.serializers import StudentProfileSerializer, AlumniProfileSerializer


class ReviewerDetailSerializer(serializers.Serializer):
    """Nested serializer for reviewer user details."""
    sqid = serializers.CharField(source="reviewer.sqid", read_only=True)
    email = serializers.EmailField(source="reviewer.email", read_only=True)
    role = serializers.CharField(source="reviewer.role", read_only=True)
    profile = serializers.SerializerMethodField()
    
    def get_profile(self, obj):
        profile = obj.reviewer.profile
        if profile is None:
            return None
        
        if obj.reviewer.role == "student":
            return StudentProfileSerializer(profile).data
        elif obj.reviewer.role == "alumni":
            return AlumniProfileSerializer(profile).data
        
        return None


class RevieweeDetailSerializer(serializers.Serializer):
    """Nested serializer for reviewee user details."""
    sqid = serializers.CharField(source="reviewee.sqid", read_only=True)
    email = serializers.EmailField(source="reviewee.email", read_only=True)
    role = serializers.CharField(source="reviewee.role", read_only=True)
    profile = serializers.SerializerMethodField()
    
    def get_profile(self, obj):
        profile = obj.reviewee.profile
        if profile is None:
            return None
        
        if obj.reviewee.role == "student":
            return StudentProfileSerializer(profile).data
        elif obj.reviewee.role == "alumni":
            return AlumniProfileSerializer(profile).data
        
        return None


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for reading reviews."""
    reviewer_detail = ReviewerDetailSerializer(source="*", read_only=True)
    reviewee_detail = RevieweeDetailSerializer(source="*", read_only=True)
    
    class Meta:
        model = Review
        fields = [
            "sqid",
            "reviewer_detail",
            "reviewee_detail",
            "overall_rating",
            "review_text",
            "metrics",
            "editable_until",
            "created_at",
            "updated_at"
        ]
        read_only_fields = fields


class CreateReviewSerializer(serializers.Serializer):
    """Serializer for creating reviews."""
    reviewee = serializers.PrimaryKeyRelatedField(
        queryset=None,  # Validation will check role compatibility
        required=True
    )
    source_content_type_id = serializers.IntegerField(required=True)
    source_object_id = serializers.IntegerField(required=True)
    metrics = serializers.JSONField(required=False, default=dict)
    review_text = serializers.CharField(required=False, allow_blank=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set the queryset for reviewee
        from core.models import User
        self.fields["reviewee"].queryset = User.objects.all()
    
    def validate_reviewee(self, value):
        """Ensure reviewee is not the same as reviewer."""
        if self.context.get("request"):
            if value == self.context["request"].user:
                raise serializers.ValidationError("You cannot review yourself.")
        return value
    
    def create(self, validated_data):
        reviewer = self.context["request"].user
        reviewee = validated_data["reviewee"]
        source_ct_id = validated_data["source_content_type_id"]
        source_object_id = validated_data["source_object_id"]
        metrics = validated_data.get("metrics", {})
        review_text = validated_data.get("review_text", "")
        
        review = create_review(
            reviewer=reviewer,
            reviewee=reviewee,
            source_ct_id=source_ct_id,
            source_object_id=source_object_id,
            metrics=metrics,
            review_text=review_text
        )
        
        return review


class UpdateReviewSerializer(serializers.Serializer):
    """Serializer for updating reviews."""
    metrics = serializers.JSONField(required=False)
    review_text = serializers.CharField(required=False, allow_blank=True)
    
    def update(self, instance, validated_data):
        metrics = validated_data.get("metrics")
        review_text = validated_data.get("review_text")
        
        return update_review(
            review=instance,
            metrics=metrics,
            review_text=review_text
        )
