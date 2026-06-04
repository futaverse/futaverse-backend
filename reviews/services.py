from django.utils import timezone
from django.db.models import Avg, Count
from datetime import timedelta

from reviews.models import Review

def create_review(
    reviewer,
    reviewee,
    engagement,
    metrics=None,
    review_text="",
    overall_rating=None
):
    review = Review.objects.create(
        reviewer=reviewer,
        reviewee=reviewee,
        source=engagement,
        metrics=metrics,
        overall_rating=overall_rating,
        review_text=review_text,
        editable_until=timezone.now() + timedelta(days=7),
    )

    review.refresh_from_db()
    recalculate_profile_rating(reviewee)

    return review
    

# def update_review(*, review, metrics=None, review_text=None):
#     """
#     Update an existing review (text and/or metrics).
    
#     1. Check timezone.now() <= review.editable_until
#     2. Re-validate metrics via plugin if applicable
#     3. Recompute overall_rating
#     4. Save
#     5. Call recalculate_profile_rating(review.reviewee)
    
#     Args:
#         review: Review instance to update
#         metrics: dict of updated metrics (optional)
#         review_text: Updated review text (optional)
    
#     Returns:
#         Updated Review instance
    
#     Raises:
#         ValidationError: if review is no longer editable or validation fails
#     """
#     # Check if review is still editable
#     if timezone.now() > review.editable_until:
#         raise ValidationError("Review can no longer be edited.")
    
#     # Update fields if provided
#     if review_text is not None:
#         review.review_text = review_text
    
#     if metrics is not None:
#         plugin = get_plugin(review.source_content_type_id, review.reviewer.role)
#         if plugin:
#             validated_metrics = plugin.validate_metrics(metrics)
#             computed_rating = plugin.compute_overall(validated_metrics)
#             review.metrics = validated_metrics
#             review.overall_rating = computed_rating
#         else:
#             raise ValidationError(
#                 "Cannot update metrics when no plugin is registered for this review type."
#             )
    
#     review.save()
#     recalculate_profile_rating(review.reviewee)
    
#     return review


def recalculate_profile_rating(reviewee):
    """
    Recalculate and cache avg_rating and total_reviews on reviewee's profile.
    
    Aggregates all reviews for the reviewee and updates the profile's
    avg_rating and total_reviews fields via .update() (not a full save).
    
    Args:
        reviewee: User instance
    """
    from reviews.models import Review
    
    reviews_data = Review.objects.filter(reviewee=reviewee).aggregate(
        avg_rating=Avg("overall_rating"),
        total_reviews=Count("id")
    )
    
    avg_rating = reviews_data.get("avg_rating")
    total_reviews = reviews_data.get("total_reviews", 0)
    
    profile = reviewee.profile
    if profile:
        profile.__class__.objects.filter(pk=profile.pk).update(
            avg_rating=avg_rating,
            total_reviews=total_reviews
        )