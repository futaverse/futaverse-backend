from internships.models import InternshipEngagement
from internships.serializers import InternshipEngagementFeedSerializer

from mentorships.models import MentorshipEngagement
from mentorships.serializers import MentorshipEngagementFeedSerializer

from feed.models import FeedEvent

def humanize_list(items):
    if len(items) == 1:
        return items[0]
    return ', '.join(items[:-1]) + f' and {items[-1]}' 

POST_PLUGINS = { #TODO: Move this to a more appropriate place, maybe a registry in the feed app or something like that. Also, work on the default text. Use def register_post_plugin(model_class, serializer, default_text, feed_event, model_key):
    InternshipEngagement: {
        "serializer": InternshipEngagementFeedSerializer,
        "default_text": lambda context: (
            f"I'm excited to share that I've just started a new internship "
            f"at {context['company']} as a {context['title']}!"
        ),
        "feed_event": FeedEvent.EventType.INTERNSHIP_STARTED,
        "model": "internship_engagement",
    },
    
    MentorshipEngagement: {
        "serializer": MentorshipEngagementFeedSerializer,
        "default_text": lambda context:  (
            f"Excited to share that I've just started a mentorship journey in the"
            f"{context['category']} field with a FUTA alumnus! Looking forward to to learning and growing."
            # f"in {humanize_list(context['focus_areas'])}."
        ),
        "feed_event": FeedEvent.EventType.MENTORSHIP_STARTED,
        "model": "mentorship_engagement",
    },
}