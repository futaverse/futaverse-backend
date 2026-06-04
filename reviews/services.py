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
    

def update_review(review, metrics=None, review_text=None, overall_rating=None):
    if review_text is not None:
        review.review_text = review_text
    
    if metrics is not None:
        review.metrics = metrics
        review.overall_rating = overall_rating
    
    review.save(update_fields=["review_text", "metrics", "overall_rating", "updated_at"])
    
    review.refresh_from_db()
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