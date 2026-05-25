from internships.models import InternshipEngagement
from internships.serializers import InternshipEngagementFeedSerializer

from mentorships.models import MentorshipEngagement
from mentorships.serializers import MentorshipEngagementFeedSerializer

POST_RELATED_SERIALIZERS = {
    InternshipEngagement: InternshipEngagementFeedSerializer,
    MentorshipEngagement: MentorshipEngagementFeedSerializer,
}