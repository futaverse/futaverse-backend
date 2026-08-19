import random

from django.db import models

from core.models import User
from futaverse.models import BaseModel


class FeedEvent(BaseModel):
    class EventType(models.TextChoices):
        INTERNSHIP_CREATED = "internship_created", "Internship created"
        MENTORSHIP_CREATED = "mentorship_created", "Mentorship created"
        EVENT_CREATED = "event_created", "Event created"

        INTERNSHIP_STARTED = "internship_started", "Internship started"
        MENTORSHIP_STARTED = "mentorship_started", "Mentorship started"

        INTERNSHIP_COMPLETED = "internship_completed", "Internship completed"
        MENTORSHIP_COMPLETED = "mentorship_completed", "Mentorship completed"

    class Audience(models.TextChoices):
        PUBLIC = "public", "Public"
        STUDENT = "student", "Student"
        ALUMNI = "alumni", "Alumni"

    event_type = models.CharField(max_length=50, choices=EventType.choices)
    audience = models.CharField(
        choices=Audience.choices, max_length=20, default=Audience.PUBLIC
    )
    data = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    score = models.IntegerField(default=0)
    # TEMPORARY STOPGAP: shuffle_seed is a one-time random float [0,1) assigned at creation.
    # It acts as a tiebreaker within the same score bucket to prevent event-type
    # clustering. This is NOT dynamic randomization — the order is fixed after creation.
    # When a proper content-diversity/ranking algorithm is implemented (e.g. ML-based
    # relevance, engagement-weighted scoring, or category-level capping), remove this
    # field, restore the index to ["-score", "-created_at"], and simplify the sort.
    shuffle_seed = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-score", "shuffle_seed"]),
        ]

    def save(self, *args, **kwargs):
        if self.shuffle_seed is None:
            self.shuffle_seed = random.random()
        super().save(*args, **kwargs)


class FeedTarget(models.Model):
    class TARGET_TYPES(models.TextChoices):
        SKILL = "skill", "Skill"
        DEPARTMENT = "department", "Department"
        LEVEL = "level", "Level"
        FACULTY = "faculty", "Faculty"
        INDUSTRY = "industry", "Industry"
        COMPANY_TYPE = "company_type", "Company Type"
        CATEGORY = "category", "Category"

    event = models.ForeignKey(
        FeedEvent, on_delete=models.CASCADE, related_name="targets"
    )
    target_type = models.CharField(max_length=50, choices=TARGET_TYPES)
    target_value = models.CharField(max_length=100)

    class Meta:
        unique_together = [("event", "target_type", "target_value")]
        indexes = [
            models.Index(fields=["target_type", "target_value"]),
        ]

    def __str__(self):
        return f"{self.target_type}={self.target_value} → event#{self.event.sqid}"


class FeedImpression(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="feed_impressions"
    )
    event = models.ForeignKey(
        FeedEvent, on_delete=models.CASCADE, related_name="impressions"
    )
    seen_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "event")]
        indexes = [
            models.Index(fields=["user", "event"]),
        ]

    def __str__(self):
        return f"{self.user_id} saw event#{self.event.sqid}"
