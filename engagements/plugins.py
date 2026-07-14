from internships.models import InternshipEngagement
from internships.serializers import InternshipEngagementFeedSerializer

from mentorships.models import MentorshipEngagement
from mentorships.serializers import MentorshipEngagementFeedSerializer

from feed.models import FeedEvent

def humanize_list(items):
    if len(items) == 1:
        return items[0]
    return ', '.join(items[:-1]) + f' and {items[-1]}' 

# The engagement plugin registry maps model classes to serializers and feed metadata.
# This lives in engagements/ because engagements is the shared layer that both
# internships and mentorships depend on. To add a new engagement type, register
# it in ENGAGEMENT_PLUGIN below and add to futaverse/lib.py MODELS dict.

_internship_engagement_plugin = {
    "serializer":   InternshipEngagementFeedSerializer,
    "default_text": lambda context: (
        f"I'm excited to share that I've just started a new internship "
        f"at {context['company']} as a {context['title']}!"
    ),
    "default_completion_text": lambda context: (
        f"I'm thrilled to announce that I've successfully completed my internship "
        f"at {context['company']} as a {context['title']}!"
    ),
    "feed_event":  FeedEvent.EventType.INTERNSHIP_STARTED,
    "model":   "internship_engagement",
    "domain":      "internship",
}

_mentorship_engagement_plugin = {
    "serializer":   MentorshipEngagementFeedSerializer,
    "default_text": lambda context: (
        f"Excited to share that I've just started a mentorship journey in the "
        f"{context['category']} field with a FUTA alumnus! "
        f"Looking forward to learning and growing."
    ),
    "default_completion_text": lambda context: (
        f"Excited to share that I've successfully completed my mentorship journey in the "
        f"{context['category']} field with a FUTA alumnus! "
        f"Looking back on the experience, I'm grateful for the guidance and support."
    ),
    "feed_event":  FeedEvent.EventType.MENTORSHIP_STARTED,
    "model":   "mentorship_engagement",
    "domain":      "mentorship",
}

ENGAGEMENT_PLUGIN = {
    InternshipEngagement:      _internship_engagement_plugin,
    "internship_engagement":   _internship_engagement_plugin,

    MentorshipEngagement:      _mentorship_engagement_plugin,
    "mentorship_engagement":   _mentorship_engagement_plugin,
}

def get_engagement_plugin(key):
    return ENGAGEMENT_PLUGIN.get(key)