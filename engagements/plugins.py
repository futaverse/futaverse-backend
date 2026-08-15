from internships.serializers import InternshipEngagementFeedSerializer
from mentorships.serializers import MentorshipEngagementFeedSerializer

from engagements.models import Engagement

# Serializer registry for engagement feed rendering, keyed by the single
# canonical EngagementType. Display text, feed event mapping and domain names
# live in engagements/services.py.
ENGAGEMENT_PLUGIN = {
    Engagement.EngagementType.INTERNSHIP: {
        "serializer": InternshipEngagementFeedSerializer,
    },
    Engagement.EngagementType.MENTORSHIP: {
        "serializer": MentorshipEngagementFeedSerializer,
    },
}


def get_engagement_plugin(key):
    return ENGAGEMENT_PLUGIN.get(key)
