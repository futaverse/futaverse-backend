from django.db import transaction

from celery import shared_task

from .models import FeedImpression, FeedEvent, FeedTarget
from futaverse.lib import MODELS

@shared_task
def record_impressions_task(user_id, event_ids):
    impressions = [
        FeedImpression(user_id=user_id, event_id=event_id)
        for event_id in event_ids
    ]
    FeedImpression.objects.bulk_create(impressions, ignore_conflicts=True)
    
    
@shared_task
def create_feed_event_task(event_type, related_object_id, related_model, data, audience="public"):
    """
    Resolves the related object and creates the feed event in the background.
    related_model is a string like 'internship'
    """
    print(f"Creating feed event: {event_type}")
    
    model = MODELS.get(related_model)
    if not model:
        raise ValueError(f"Unknown related model: {related_model}")
    
    related_object = model.objects.get(id=related_object_id)

    with transaction.atomic():
        event = FeedEvent.objects.create(event_type=event_type, data=data, audience=audience)

        targets = getattr(related_object, 'feed_targets', [])
        if targets:
            print(f"Creating {len(targets)} feed targets")
            FeedTarget.objects.bulk_create([
                FeedTarget(event=event, **target) for target in targets
            ])