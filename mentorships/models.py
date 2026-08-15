from django.db import models
from core.models import AlumniProfile, StudentProfile
from futaverse.models import BaseModel
from django.utils import timezone

from engagements.models import Engagement, BaseApplication, BaseOffer, EngagementLifecycleStatus


class FocusArea(models.TextChoices):
        CAREER_GUIDANCE       = 'career_guidance',       'Career Guidance'
        CV_AND_PORTFOLIO      = 'cv_and_portfolio',      'CV & Portfolio Building'
        INTERVIEW_PREP        = 'interview_prep',        'Interview Preparation'
        LINKEDIN_BRANDING     = 'linkedin_branding',     'LinkedIn & Personal Branding'
        SALARY_NEGOTIATION    = 'salary_negotiation',    'Salary Negotiation'
        SOFTWARE_ENGINEERING  = 'software_engineering',  'Software Engineering'
        DATA_SCIENCE          = 'data_science',          'Data Science & Analytics'
        PRODUCT_MANAGEMENT    = 'product_management',    'Product Management'
        PRODUCT_DESIGN        = 'product_design',        'Product Design & UX'
        CYBERSECURITY         = 'cybersecurity',         'Cybersecurity'
        CLOUD_DEVOPS          = 'cloud_devops',          'Cloud & DevOps'
        EMBEDDED_SYSTEMS      = 'embedded_systems',      'Embedded Systems & IoT'
        RESEARCH_ACADEMIA     = 'research_academia',     'Research & Academia'
        ENTREPRENEURSHIP      = 'entrepreneurship',       'Entrepreneurship'
        FREELANCING           = 'freelancing',            'Freelancing & Remote Work'
        FINTECH               = 'fintech',                'Fintech'
        AGRITECH              = 'agritech',               'Agritech'
        STARTUP_BUILDING      = 'startup_building',       'Startup Building'
        BUSINESS_DEVELOPMENT  = 'business_development',   'Business Development'
        TECH_IN_NIGERIA       = 'tech_in_nigeria',       'Breaking into Tech in Nigeria'
        DIASPORA_PATHWAYS     = 'diaspora_pathways',     'Diaspora & International Opportunities'
        POSTGRAD_ABROAD       = 'postgrad_abroad',       'Postgraduate Studies Abroad'
        NYSC_GUIDANCE         = 'nysc_guidance',         'NYSC & Early Career'
        COMMUNICATION         = 'communication',          'Communication & Presentation'
        LEADERSHIP            = 'leadership',             'Leadership & Teamwork'
        OPEN_SOURCE           = 'open_source',            'Open Source Contribution'
        OTHER                 = 'other',                  'Other'

class MentorshipCategory(models.TextChoices):
    CAREER_DEVELOPMENT = 'career_development', 'Career Development'
    TECHNICAL          = 'technical',          'Technical'
    ACADEMIC           = 'academic',           'Academic'
    ENTREPRENEURSHIP   = 'entrepreneurship',   'Entrepreneurship'
    INDUSTRY_SPECIFIC  = 'industry_specific',  'Industry Specific'
    OTHER              = 'other',              'Other'


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

    cover_letter = models.TextField(blank=False)

    def __str__(self):
        return f"Application of {self.student.full_name} for {self.mentorship.title} (mentorship)"


class MentorshipOffer(BaseOffer):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='offers')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentorship_offers')

    def __str__(self):
        return f"Offer of {self.student.full_name} for {self.mentorship.title} (mentorship)"


class MentorshipEngagement(BaseModel):
    class Source(models.TextChoices):
        APPLICATION = "application", "Application"
        OFFER = "offer", "Offer"
        REQUEST = "request", "Request"

    engagement = models.OneToOneField(
        Engagement,
        on_delete=models.CASCADE,
        related_name='mentorship_detail',
    )
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='engagements')
    application = models.ForeignKey(
        MentorshipApplication, on_delete=models.PROTECT,
        null=True, blank=True, related_name='engagements',
    )
    offer = models.ForeignKey(
        MentorshipOffer, on_delete=models.PROTECT,
        null=True, blank=True, related_name='engagements',
    )
    # Deferred: the Request origin is specified in Decision 4 of the spec. The
    # MentorshipRequest model was removed in migration 0004 and will be
    # reintroduced later; add the typed FK and extend the origin constraint then.

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(application__isnull=False, offer__isnull=True)
                    | models.Q(application__isnull=True, offer__isnull=False)
                ),
                name='mentorship_engagement_single_origin',
            )
        ]

    @property
    def post_context(self):
        return {
            "type": "mentorship",
            "title": self.mentorship.title,
            "focus_areas": self.mentorship.focus_areas,
            "category": self.mentorship.category,
        }

    def __str__(self):
        return f"Engagement of {self.engagement.student.full_name} in {self.mentorship.title}"
