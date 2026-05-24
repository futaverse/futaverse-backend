from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from futaverse.models import BaseModel
from core.models import User

class Post(BaseModel):
    class PostType(models.TextChoices):
        ENGAGEMENT_STARTED = 'engagement_started', 'Engagement Started'
        MILESTONE          = 'milestone',           'Milestone'

    author       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    post_type    = models.CharField(max_length=50, choices=PostType.choices)
    content      = models.TextField()                                        
    is_public    = models.BooleanField(default=True)

    content_type   = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    object_id      = models.PositiveIntegerField(null=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']