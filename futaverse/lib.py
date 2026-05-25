
from internships.models import Internship, InternshipEngagement
from mentorships.models import Mentorship, MentorshipEngagement
from events.models import Event

MODELS = {
    "internship": Internship,
    "mentorship": Mentorship,
    "event": Event,
    
    "internship_engagement": InternshipEngagement,
    "mentorship_engagement": MentorshipEngagement
}