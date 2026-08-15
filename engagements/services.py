from django.db import transaction

from engagements.models import Engagement

from internships.models import InternshipEngagement
from mentorships.models import MentorshipEngagement

from feed.models import FeedEvent

DETAIL_MODELS = {
    Engagement.EngagementType.INTERNSHIP: InternshipEngagement,
    Engagement.EngagementType.MENTORSHIP: MentorshipEngagement,
}

FEED_EVENT_TYPES = {
    Engagement.EngagementType.INTERNSHIP: FeedEvent.EventType.INTERNSHIP_STARTED,
    Engagement.EngagementType.MENTORSHIP: FeedEvent.EventType.MENTORSHIP_STARTED,
}

DOMAINS = {
    Engagement.EngagementType.INTERNSHIP: "internship",
    Engagement.EngagementType.MENTORSHIP: "mentorship",
}


def get_engagement_detail(engagement):
    if engagement.engagement_type not in DETAIL_MODELS:
        return None
    return engagement.detail


def get_engagement_post_context(engagement):
    detail = get_engagement_detail(engagement)
    if detail is None:
        return {}
    return detail.post_context


def default_share_text(engagement):
    context = get_engagement_post_context(engagement)
    if engagement.engagement_type == Engagement.EngagementType.INTERNSHIP:
        return (
            f"I'm excited to share that I've just started a new internship "
            f"at {context['company']} as a {context['title']}!"
        )
    if engagement.engagement_type == Engagement.EngagementType.MENTORSHIP:
        return (
            f"Excited to share that I've just started a mentorship journey in the "
            f"{context['category']} field with a FUTA alumnus! "
            f"Looking forward to learning and growing."
        )
    raise ValueError(f"Unknown engagement type: {engagement.engagement_type}")


def default_completion_text(engagement):
    context = get_engagement_post_context(engagement)
    if engagement.engagement_type == Engagement.EngagementType.INTERNSHIP:
        return (
            f"I'm thrilled to announce that I've successfully completed my internship "
            f"at {context['company']} as a {context['title']}!"
        )
    if engagement.engagement_type == Engagement.EngagementType.MENTORSHIP:
        return (
            f"Excited to share that I've successfully completed my mentorship journey in the "
            f"{context['category']} field with a FUTA alumnus! "
            f"Looking back on the experience, I'm grateful for the guidance and support."
        )
    raise ValueError(f"Unknown engagement type: {engagement.engagement_type}")


def feed_event_type(engagement):
    return FEED_EVENT_TYPES.get(engagement.engagement_type)


def engagement_domain(engagement):
    return DOMAINS.get(engagement.engagement_type, engagement.engagement_type)


def create_engagement(*, engagement_type, student, alumnus, application=None, offer=None):
    if (application is None) == (offer is None):
        raise ValueError("Exactly one of application or offer must be provided.")

    with transaction.atomic():
        engagement = Engagement.objects.create(
            engagement_type=engagement_type,
            student=student,
            alumnus=alumnus,
        )

        if engagement_type == Engagement.EngagementType.INTERNSHIP:
            listing = application.internship if application else offer.internship
            InternshipEngagement.objects.create(
                engagement=engagement,
                internship=listing,
                application=application,
                offer=offer,
            )
        elif engagement_type == Engagement.EngagementType.MENTORSHIP:
            listing = application.mentorship if application else offer.mentorship
            MentorshipEngagement.objects.create(
                engagement=engagement,
                mentorship=listing,
                application=application,
                offer=offer,
            )
        else:
            raise ValueError(f"Unknown engagement type: {engagement_type}")

    engagement.refresh_from_db()
    return engagement
