from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from core.models import StudentProfile, AlumniProfile, User
from futaverse.models import BaseModel

class Review(BaseModel):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')

    rating = models.PositiveIntegerField()
    comment = models.TextField()

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='reviews')
    object_id = models.PositiveIntegerField()
    related_object = GenericForeignKey('content_type', 'object_id')

class BaseEngagement(BaseModel):
    class EngagementStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CLOSED = "closed", "Closed"
        TERMINATED = "terminated", "Terminated"
        ARCHIVED = "archived", "Archived"

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='%(app_label)s_engagements')
    alumnus = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='%(app_label)s_engagements')
    
    source = models.CharField(max_length=20)
    source_id = models.PositiveIntegerField()
    status = models.CharField(choices=EngagementStatus.choices, max_length=20, default=EngagementStatus.ACTIVE)
    
    reviews = GenericRelation(Review, related_query_name='engagement')
    
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active(self):
        return self.status == self.EngagementStatus.ACTIVE

    @property
    def engagement(self):
        
        if hasattr(self, 'internship'):
            return self.internship
        
        if hasattr(self, 'mentorship'):
            return self.mentorship
        
        return 
    
    def mark_as_completed(self):
        self.status = self.EngagementStatus.COMPLETED
        self.save(update_fields=['status', 'updated_at'])
        
    class Meta:
        abstract = True

