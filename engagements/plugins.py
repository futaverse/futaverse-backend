from internships.models import InternshipEngagement
from internships.serializers import InternshipEngagementFeedSerializer

from mentorships.models import MentorshipEngagement
from mentorships.serializers import MentorshipEngagementFeedSerializer

from feed.models import FeedEvent

def humanize_list(items):
    if len(items) == 1:
        return items[0]
    return ', '.join(items[:-1]) + f' and {items[-1]}' 

#TODO: Move this to a more appropriate place, maybe a registry in the feed app or something like that. Also, work on the default text. Use def register_post_plugin(model_class, serializer, default_text, feed_event, model_key)

_internship_engagement_plugin = {
    "serializer":   InternshipEngagementFeedSerializer,
    "default_text": lambda context: (
        f"I'm excited to share that I've just started a new internship "
        f"at {context['company']} as a {context['title']}!"
    ),
    "feed_event":  FeedEvent.EventType.INTERNSHIP_STARTED,
    "model_key":   "internship_engagement",
    "domain":      "internship",
}

_mentorship_engagement_plugin = {
    "serializer":   MentorshipEngagementFeedSerializer,
    "default_text": lambda context: (
        f"Excited to share that I've just started a mentorship journey in the "
        f"{context['category']} field with a FUTA alumnus! "
        f"Looking forward to learning and growing."
    ),
    "feed_event":  FeedEvent.EventType.MENTORSHIP_STARTED,
    "model_key":   "mentorship_engagement",
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