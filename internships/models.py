from django.db import models
from core.models import StudentProfile, AlumniProfile
from futaverse.models import BaseModel
from django.utils import timezone

from engagements.models import BaseEngagement, BaseApplication, BaseOffer, EngagementLifecycleStatus


class Internship(BaseModel):
    class WorkMode(models.TextChoices):
        REMOTE = 'Remote', 'Remote'
        HYBRID = 'Hybrid', 'Hybrid'
        ONSITE = 'Onsite', 'Onsite'

    class EngagementType(models.TextChoices):
        FULL_TIME = 'Full-time', 'Full-time'
        PART_TIME = 'Part-time', 'Part-time'
        CONTRACT = 'Contract', 'Contract'

    alumnus = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='internships')

    title = models.CharField(max_length=255)
    description = models.TextField()
    work_mode = models.CharField(choices=WorkMode.choices, max_length=20)
    engagement_type = models.CharField(choices=EngagementType.choices, max_length=20)
    location = models.CharField(max_length=255)
    skills_required = models.JSONField(default=list, blank=True)
    duration_weeks = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    stipend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    levels = models.JSONField(default=list)

    company = models.CharField(max_length=255)
    company_type = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    company_linkedin_url = models.URLField(blank=True, null=True, max_length=200)
    company_website_url = models.URLField(blank=True, null=True, max_length=200)

    available_slots = models.PositiveIntegerField(blank=True, null=True)
    remaining_slots = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    require_resume = models.BooleanField(default=True)
    require_cover_letter = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    def toggle_active(self):
        self.is_active = not self.is_active
        self.save(update_fields=['is_active'])

    def decrement_remaining_slots(self):
        if self.available_slots is None:
            return

        if self.remaining_slots > 0:
            self.remaining_slots -= 1
            self.save(update_fields=['remaining_slots'])
            return self.remaining_slots
        return 0

    def __str__(self):
        return f"{self.title} (internship)"

    @property
    def feed_targets(self):
        targets = []

        for skill in self.skills_required:
            targets.append({'target_type': 'skill', 'target_value': skill})

        if self.industry:
            targets.append({'target_type': 'industry', 'target_value': self.industry})

        if self.company_type:
            targets.append({'target_type': 'company_type', 'target_value': self.company_type})

        return targets


class InternshipApplication(BaseApplication):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='internship_applications')

    def __str__(self):
        return f"Application of {self.student.full_name} for {self.internship.title} (internship)"


class InternshipOffer(BaseOffer):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='offers')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='internship_offers')

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Offer to {self.student.full_name} for {self.internship.title}"


class InternshipEngagement(BaseEngagement):
    class Source(models.TextChoices):
        APPLICATION = "application", "Application"
        OFFER = "offer", "Offer"

    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='engagements')

    @property
    def post_context(self):
        return {
            "type": "internship",
            "title": self.internship.title,
            "company": self.internship.company,
        }

    def __str__(self):
        return f"Engagement of {self.student.full_name} in {self.internship.title}"


class ApplicationResume(BaseModel):
    application = models.OneToOneField(InternshipApplication, on_delete=models.CASCADE, related_name='resume', blank=True, null=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.SET_NULL, related_name='application_resumes', null=True)
    resume = models.URLField(max_length=200)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.application:
            return f"Resume of {self.application.student.full_name} for {self.application.internship.title}"
        return f"Unlinked resume (ID: {self.sqid})"
