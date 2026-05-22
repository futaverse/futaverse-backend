from celery import shared_task
from .models import FeedImpression, FeedEvent, FeedTarget
from internships.models import Internship
from mentorships.models import Mentorship
from events.models import Event

MODELS = {
    "internship": Internship,
    "mentorship": Mentorship,
    "event": Event
}

@shared_task
def record_impressions_task(user_id, event_ids):
    impressions = [
        FeedImpression(user_id=user_id, event_id=event_id)
        for event_id in event_ids
    ]
    FeedImpression.objects.bulk_create(impressions, ignore_conflicts=True)
    
@shared_task
def create_feed_event_task(event_type, related_object_id, related_model, data, audience):
    """
    Resolves the related object and creates the feed event in the background.
    related_model is a string like 'internships.Internship'
    """

    Model = MODELS.get(related_model)
    related_object = Model.objects.get(id=related_object_id)

    event = FeedEvent.objects.create(event_type=event_type, data=data, audience=audience)

    targets = related_object.get_feed_targets()
    if targets:
        FeedTarget.objects.bulk_create([
            FeedTarget(event=event, **target) for target in targets
        ])