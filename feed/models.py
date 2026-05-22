from django.db import models

from futaverse.models import BaseModel, User

# Create your models here.


class FeedEvent(BaseModel):
    class EventType(models.TextChoices):
        INTERNSHIP_CREATED = "internship_created", "Internship created"
        MENTORSHIP_CREATED = "mentorship_created", "Mentorship created"
        EVENT_CREATED = "event_created", "Event created"
        
    class Audience(models.TextChoices):
        PUBLIC = "public", "Public"
        STUDENTS = "students", "Students"
        ALUMNI = "alumni", "Alumni"

    event_type = models.CharField(max_length=50, choices=EventType.choices)
    audience = models.CharField(choices=Audience.choices, max_length=20, default=Audience.PUBLIC)
    data = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)   
    
    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),
        ]

class FeedTarget(models.Model):
    class TARGET_TYPES(models.TextChoices):
        SKILL = "skill", "Skill"
        DEPARTMENT = "department", "Department"
        LEVEL = "level", "Level"
        FACULTY = "faculty", "Faculty"
        INDUSTRY = "industry", "Industry"
        COMPANY_TYPE = "company_type", "Company Type"
    
    event        = models.ForeignKey(FeedEvent, on_delete=models.CASCADE, related_name='targets')
    target_type  = models.CharField(max_length=50, choices=TARGET_TYPES)
    target_value = models.CharField(max_length=100)

    class Meta:
        unique_together = [('event', 'target_type', 'target_value')]
        indexes = [
            models.Index(fields=['target_type', 'target_value']),
        ]

    def __str__(self):
        return f"{self.target_type}={self.target_value} → event#{self.event.sqid}"
    
class FeedImpression(models.Model):
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feed_impressions')
    event   = models.ForeignKey(FeedEvent, on_delete=models.CASCADE, related_name='impressions')
    seen_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'event')]
        indexes = [
            models.Index(fields=['user', 'event']),
        ]

    def __str__(self):
        return f"{self.user_id} saw event#{self.event.sqid}"
