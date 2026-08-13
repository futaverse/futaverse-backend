from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from core.models import StudentProfile, AlumniProfile
from futaverse.models import BaseModel

from reviews.models import Review


class Engagement(BaseModel):
    class EngagementType(models.TextChoices):
        INTERNSHIP = "internship_engagement", "Internship"
        MENTORSHIP = "mentorship_engagement", "Mentorship"

    class EngagementStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        TERMINATED = "terminated", "Terminated"
        ARCHIVED = "archived", "Archived"

    engagement_type = models.CharField(choices=EngagementType.choices, max_length=30)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='engagements')
    alumnus = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='engagements')

    status = models.CharField(choices=EngagementStatus.choices, max_length=20, default=EngagementStatus.ACTIVE)

    reviews = GenericRelation(Review, related_query_name='engagement')

    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_status_active(self):
        return self.status == self.EngagementStatus.ACTIVE

    @property
    def detail(self):
        related_name = f"{self.engagement_type.removesuffix('_engagement')}_detail"
        return getattr(self, related_name, None)

    def update_status(self, status):
        self.status = status
        self.save(update_fields=['status', 'updated_at'])

    def __str__(self):
        return f"Engagement of {self.student.full_name} with {self.alumnus.full_name} ({self.engagement_type})"


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
        internship = getattr(self, 'internship', None)
        if internship is not None:
            return internship
        mentorship = getattr(self, 'mentorship', None)
        if mentorship is not None:
            return mentorship
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
        if self.status != EngagementLifecycleStatus.PENDING:
            raise ValueError(f"Cannot accept application with status '{self.status}'. Expected 'pending'.")
        self.status = EngagementLifecycleStatus.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def reject(self):
        if self.status != EngagementLifecycleStatus.PENDING:
            raise ValueError(f"Cannot reject application with status '{self.status}'. Expected 'pending'.")
        self.status = EngagementLifecycleStatus.REJECTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def withdraw(self):
        if self.status != EngagementLifecycleStatus.PENDING:
            raise ValueError(f"Cannot withdraw application with status '{self.status}'. Expected 'pending'.")
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
        if self.status != EngagementLifecycleStatus.PENDING:
            raise ValueError(f"Cannot accept offer with status '{self.status}'. Expected 'pending'.")
        self.status = EngagementLifecycleStatus.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def reject(self):
        if self.status != EngagementLifecycleStatus.PENDING:
            raise ValueError(f"Cannot reject offer with status '{self.status}'. Expected 'pending'.")
        self.status = EngagementLifecycleStatus.REJECTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def withdraw(self):
        if self.status != EngagementLifecycleStatus.PENDING:
            raise ValueError(f"Cannot withdraw offer with status '{self.status}'. Expected 'pending'.")
        self.status = EngagementLifecycleStatus.WITHDRAWN
        self.save(update_fields=["status"])
