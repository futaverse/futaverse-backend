from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings

from futaverse.models import BaseModel

class Review(BaseModel):
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_given"
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_received"
    )
    
    source_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    source_object_id = models.PositiveIntegerField()
    source = GenericForeignKey("source_content_type", "source_object_id")
    
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2)
    review_text = models.TextField(blank=True)
    metrics = models.JSONField(default=dict)
    editable_until = models.DateTimeField()
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ("reviewer", "reviewee", "source_content_type", "source_object_id")
    
    def __str__(self):
        return f"Review by {self.reviewer.email} for {self.reviewee.email}"
