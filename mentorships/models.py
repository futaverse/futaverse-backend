from django.db import models
from core.models import AlumniProfile, StudentProfile
from futaverse.models import BaseModel
from django.utils import timezone
from .lib import FocusArea, MentorshipCategory

from engagements.models import BaseEngagement, BaseApplication, BaseOffer, EngagementLifecycleStatus


class Mentorship(BaseModel):
    class WorkMode(models.TextChoices):
        REMOTE = 'Remote', 'Remote'
        HYBRID = 'Hybrid', 'Hybrid'
        ONSITE = 'Onsite', 'Onsite'

    alumnus = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='mentorships')
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=MentorshipCategory.choices)
    focus_areas = models.JSONField(default=list, blank=True)

    work_mode = models.CharField(choices=WorkMode.choices, max_length=20, default=WorkMode.REMOTE, blank=True)
    duration_weeks = models.PositiveIntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    available_slots = models.PositiveIntegerField(blank=True, null=True)
    remaining_slots = models.PositiveIntegerField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (mentorship)"

    def decrement_remaining_slots(self):
        if self.remaining_slots is None:
            return
        if self.remaining_slots > 0:
            self.remaining_slots -= 1
            self.save(update_fields=['remaining_slots'])
            return self.remaining_slots
        return 0

    def toggle_active(self):
        self.is_active = not self.is_active
        self.save(update_fields=['is_active'])

    @property
    def feed_targets(self):
        targets = []

        for area in self.focus_areas:
            targets.append({'target_type': 'skill', 'target_value': area})

        if self.category:
            targets.append({'target_type': 'category', 'target_value': self.category})

        return targets


class MentorshipApplication(BaseApplication):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentorship_applications')

    cover_letter = models.TextField()

    def __str__(self):
        return f"Application of {self.student.full_name} for {self.mentorship.title} (mentorship)"


class MentorshipOffer(BaseOffer):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='offers')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentorship_offers')

    def __str__(self):
        return f"Offer of {self.student.full_name} for {self.mentorship.title} (mentorship)"


class MentorshipRequest(BaseOffer):
    mentor = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='mentorship_requests')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentorship_requests')
    message = models.TextField()

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request by {self.student.full_name} to {self.mentor.full_name}"


class MentorshipEngagement(BaseEngagement):
    class Source(models.TextChoices):
        APPLICATION = "application", "Application"
        OFFER = "offer", "Offer"
        REQUEST = "request", "Request"

    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='engagements')

    @property
    def post_context(self):
        return {
            "type": "mentorship",
            "title": self.mentorship.title,
            "focus_areas": self.mentorship.focus_areas,
            "category": self.mentorship.category,
        }

    def __str__(self):
        return f"Engagement of {self.student.full_name} in {self.mentorship.title}"
