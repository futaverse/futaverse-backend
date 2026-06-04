from rest_framework.exceptions import NotFound

from reviews.models import Review

def get_review(review_id):
    """
    Get a single review by ID.
    
    Args:
        review_id: ID of the review
    
    Returns:
        Review instance
    
    Raises:
        NotFound: if review does not exist
    """
    try:
        return Review.objects.get(pk=review_id)
    except Review.DoesNotExist:
        raise NotFound("Review not found.")


def get_review_for_source(source_content_type_id, source_object_id, reviewer):
    """
    Get a review for a specific (source, reviewer) pair, or None if not found.
    
    Args:
        source_content_type_id: ContentType ID of the source
        source_object_id: ID of the source object
        reviewer: User instance (the reviewer)
    
    Returns:
        Review instance or None
    """
    try:
        return Review.objects.get(
            source_content_type_id=source_content_type_id,
            source_object_id=source_object_id,
            reviewer=reviewer
        )
    except Review.DoesNotExist:
        return None
