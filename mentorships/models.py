from django.db import models
from core.models import AlumniProfile, StudentProfile
from futaverse.models import BaseModel
from django.utils import timezone
from .lib import FocusArea

class MentorshipStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    REJECTED = 'rejected', 'Rejected'
    WITHDRAWN = 'withdrawn', 'Withdrawn'
    
class Mentorship(BaseModel):
    class WorkMode(models.TextChoices):
        REMOTE = 'Remote', 'Remote'
        HYBRID = 'Hybrid', 'Hybrid'
        ONSITE = 'Onsite', 'Onsite'
    
    alumnus = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='mentorships')
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=FocusArea.choices)
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
        return targets
    
class MentorshipApplication(BaseModel):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentorship_applications')
    
    cover_letter = models.TextField()
    status = models.CharField(choices=MentorshipStatus.choices, max_length=20, default=MentorshipStatus.PENDING)
    
    responded_at = models.DateTimeField(null=True, blank=True)
    
    def withdraw(self):
        self.status = MentorshipStatus.WITHDRAWN
        self.save(update_fields=['status'])
      
    def accept(self):
        self.status = MentorshipStatus.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])
        
    def reject(self):
        self.status = MentorshipStatus.REJECTED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])

    def __str__(self):
        return f"Application of {self.student.full_name} for {self.mentorship.title} (mentorship)"
    
class MentorshipOffer(BaseModel):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='offers')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentorship_offers')
    
    status = models.CharField(choices=MentorshipStatus.choices, max_length=20, default=MentorshipStatus.PENDING)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    def withdraw(self):
        self.status = MentorshipStatus.WITHDRAWN
        self.save(update_fields=['status'])
      
    def accept(self):
        self.status = MentorshipStatus.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])
        
    def reject(self):   
        self.status = MentorshipStatus.REJECTED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])

    def __str__(self):
        return f"Offer of {self.student.full_name} for {self.mentorship.title} (mentorship)"
    
class MentorshipRequest(BaseModel):
    mentor = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='mentorship_requests')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentorship_requests')
    message = models.TextField()
    
    status = models.CharField(choices=MentorshipStatus.choices, max_length=20, default=MentorshipStatus.PENDING)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def withdraw(self):
        self.status = MentorshipStatus.WITHDRAWN
        self.save(update_fields=['status'])
        
    def accept(self):
        self.status = MentorshipStatus.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])
        
    def reject(self):
        self.status = MentorshipStatus.REJECTED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])
        
class MentorshipEngagement(BaseModel):
    class Source(models.TextChoices):
        APPLICATION = "application", "Application"
        OFFER = "offer", "Offer",
        REQUEST = "request", "Request"
        
    class EngagementStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        TERMINATED = "terminated", "Terminated"
        ARCHIVED = "archived", "Archived"
        
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='engagements')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentorship_engagements')
    alumnus = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='mentorship_engagements')    
    
    source = models.CharField(choices=Source.choices, max_length=20)
    source_id = models.PositiveIntegerField()
    status = models.CharField(choices=EngagementStatus.choices, max_length=20, default=EngagementStatus.ACTIVE)
    
    @property
    def engagement(self):
        source = self.source
        if source == self.Source.APPLICATION:
            return MentorshipApplication.objects.filter(pk=self.source_id).first()
        elif source == self.Source.OFFER:
            return MentorshipOffer.objects.filter(pk=self.source_id).first()
        elif source == self.Source.REQUEST:
            return MentorshipRequest.objects.filter(pk=self.source_id).first()
        
    @property
    def is_active(self):
        return self.status == self.EngagementStatus.ACTIVE
    
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


