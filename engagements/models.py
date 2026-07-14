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
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
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
    def is_status_active(self):
        return self.status == self.EngagementStatus.ACTIVE

    @property
    def engagement(self):
        if hasattr(self, 'internship'):
            return self.internship
        if hasattr(self, 'mentorship'):
            return self.mentorship
        return None
    
    def update_status(self, status):
        self.status = status
        self.save(update_fields=['status', 'updated_at'])
        
    class Meta:
        abstract = True


class EngagementLifecycleStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    WITHDRAWN = "withdrawn", "Withdrawn"


class BaseApplication(BaseModel):
    status = models.CharField(
        choices=EngagementLifecycleStatus.choices,
        max_length=20,
        default=EngagementLifecycleStatus.PENDING,
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    cover_letter = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    def accept(self):
        self.status = EngagementLifecycleStatus.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def reject(self):
        self.status = EngagementLifecycleStatus.REJECTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def withdraw(self):
        self.status = EngagementLifecycleStatus.WITHDRAWN
        self.save(update_fields=["status"])


class BaseOffer(BaseModel):
    status = models.CharField(
        choices=EngagementLifecycleStatus.choices,
        max_length=20,
        default=EngagementLifecycleStatus.PENDING,
    )
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def accept(self):
        self.status = EngagementLifecycleStatus.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def reject(self):
        self.status = EngagementLifecycleStatus.REJECTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def withdraw(self):
        self.status = EngagementLifecycleStatus.WITHDRAWN
        self.save(update_fields=["status"])
