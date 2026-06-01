from decimal import Decimal
from django.utils import timezone
from django.db.models import Avg, Count
from datetime import timedelta

from rest_framework.exceptions import ValidationError

from reviews.models import Review
from reviews.plugins import get_plugin


def create_review(
    *,
    reviewer,
    reviewee,
    source_ct_id,
    source_object_id,
    metrics=None,
    review_text="",
    overall_rating=None
):
    """
    Create a new review with validation and metric computation.
    
    1. Resolve plugin using (source_ct_id, reviewer.role)
    2. If source is an engagement, validate its status is ACKNOWLEDGED
    3. If plugin exists: validate metrics, compute overall_rating from plugin
    4. If no plugin: use provided overall_rating directly
    5. Set editable_until = now + timedelta(days=7)
    6. Save review
    7. Call recalculate_profile_rating(reviewee)
    
    Args:
        reviewer: User instance (the reviewer)
        reviewee: User instance (the person being reviewed)
        source_ct_id: ContentType ID of the source (e.g., InternshipEngagement)
        source_object_id: ID of the source object
        metrics: dict of metric scores (optional, depends on plugin)
        review_text: Text of the review (optional)
        overall_rating: Decimal score (required if no plugin exists)
    
    Returns:
        Review instance
    
    Raises:
        ValidationError: if validation fails at any step
    """
    if metrics is None:
        metrics = {}
    
    # Resolve plugin
    plugin = get_plugin(source_ct_id, reviewer.role)
    
    # Validate engagement status if source is an engagement
    _validate_engagement_status(source_ct_id, source_object_id)
    
    # Compute or validate overall rating
    if plugin:
        validated_metrics = plugin.validate_metrics(metrics)
        computed_rating = plugin.compute_overall(validated_metrics)
        metrics = validated_metrics
        overall_rating = computed_rating
    else:
        if overall_rating is None:
            raise ValidationError(
                "overall_rating is required when no plugin is registered for this review type."
            )
        overall_rating = Decimal(str(overall_rating))
    
    # Set editable_until
    editable_until = timezone.now() + timedelta(days=7)
    
    # Create and save review
    review = Review.objects.create(
        reviewer=reviewer,
        reviewee=reviewee,
        source_content_type_id=source_ct_id,
        source_object_id=source_object_id,
        overall_rating=overall_rating,
        review_text=review_text,
        metrics=metrics,
        editable_until=editable_until
    )
    
    # Recalculate profile rating
    recalculate_profile_rating(reviewee)
    
    return review


def update_review(*, review, metrics=None, review_text=None):
    """
    Update an existing review (text and/or metrics).
    
    1. Check timezone.now() <= review.editable_until
    2. Re-validate metrics via plugin if applicable
    3. Recompute overall_rating
    4. Save
    5. Call recalculate_profile_rating(review.reviewee)
    
    Args:
        review: Review instance to update
        metrics: dict of updated metrics (optional)
        review_text: Updated review text (optional)
    
    Returns:
        Updated Review instance
    
    Raises:
        ValidationError: if review is no longer editable or validation fails
    """
    # Check if review is still editable
    if timezone.now() > review.editable_until:
        raise ValidationError("Review can no longer be edited.")
    
    # Update fields if provided
    if review_text is not None:
        review.review_text = review_text
    
    if metrics is not None:
        plugin = get_plugin(review.source_content_type_id, review.reviewer.role)
        if plugin:
            validated_metrics = plugin.validate_metrics(metrics)
            computed_rating = plugin.compute_overall(validated_metrics)
            review.metrics = validated_metrics
            review.overall_rating = computed_rating
        else:
            raise ValidationError(
                "Cannot update metrics when no plugin is registered for this review type."
            )
    
    # Save and recalculate
    review.save()
    recalculate_profile_rating(review.reviewee)
    
    return review


def recalculate_profile_rating(reviewee):
    """
    Recalculate and cache avg_rating and total_reviews on reviewee's profile.
    
    Aggregates all reviews for the reviewee and updates the profile's
    avg_rating and total_reviews fields via .update() (not a full save).
    
    Args:
        reviewee: User instance
    """
    from reviews.models import Review
    
    # Aggregate reviews
    reviews_data = Review.objects.filter(reviewee=reviewee).aggregate(
        avg_rating=Avg("overall_rating"),
        total_reviews=Count("id")
    )
    
    avg_rating = reviews_data.get("avg_rating")
    total_reviews = reviews_data.get("total_reviews", 0)
    
    # Update profile
    profile = reviewee.profile
    if profile:
        profile.__class__.objects.filter(pk=profile.pk).update(
            avg_rating=avg_rating,
            total_reviews=total_reviews
        )


def _validate_engagement_status(source_ct_id, source_object_id):
    """
    Validate that the source (if an engagement) has status ACKNOWLEDGED.
    
    Args:
        source_ct_id: ContentType ID
        source_object_id: ID of the source object
    
    Raises:
        ValidationError: if source is an engagement and status is not ACKNOWLEDGED
    """
    from django.contrib.contenttypes.models import ContentType
    
    try:
        content_type = ContentType.objects.get(pk=source_ct_id)
    except ContentType.DoesNotExist:
        raise ValidationError("Invalid source content type.")
    
    # Check if this is an engagement by looking for status attribute
    model_class = content_type.model_class()
    
    if model_class is None:
        raise ValidationError("Invalid source content type.")
    
    try:
        source_object = model_class.objects.get(pk=source_object_id)
    except model_class.DoesNotExist:
        raise ValidationError("Source object not found.")
    
    # If the model has a status field, check it
    if hasattr(source_object, "status"):
        if not hasattr(source_object, "Status"):
            raise ValidationError("Source engagement has no Status choices defined.")
        
        # Expect the status to be ACKNOWLEDGED
        if hasattr(source_object.Status, "ACKNOWLEDGED"):
            acknowledged_status = source_object.Status.ACKNOWLEDGED
        else:
            raise ValidationError("Source engagement has no ACKNOWLEDGED status.")
        
        if source_object.status != acknowledged_status:
            raise ValidationError(
                f"Review can only be created when engagement status is ACKNOWLEDGED. "
                f"Current status: {source_object.status}"
            )
