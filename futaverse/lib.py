from internships.models import Internship
from mentorships.models import Mentorship
from events.models import Event
from posts.models import Post

from engagements.models import Engagement

MODELS = {
    "internship": Internship,
    "mentorship": Mentorship,
    "event": Event,

    "internship_engagement": Engagement,
    "mentorship_engagement": Engagement,

    "post": Post,
}
