import logging

from django.db import transaction

from futaverse.lib import MODELS

from .models import FeedEvent, FeedImpression, FeedTarget

logger = logging.getLogger(__name__)


def record_impressions_task(user_id, event_ids):
    impressions = [
        FeedImpression(user_id=user_id, event_id=event_id) for event_id in event_ids
    ]
    FeedImpression.objects.bulk_create(impressions, ignore_conflicts=True)


def create_feed_event_task(
    event_type, related_object_id, related_model, data, audience="public"
):
    model = MODELS.get(related_model)
    if not model:
        logger.error("create_feed_event_task: unknown model %s", related_model)
        return

    try:
        related_object = model.objects.get(id=related_object_id)
    except model.DoesNotExist:
        logger.error(
            "create_feed_event_task: %s %s not found", related_model, related_object_id
        )
        return

    with transaction.atomic():
        event = FeedEvent.objects.create(
            event_type=event_type, data=data, audience=audience
        )

        targets = getattr(related_object, "feed_targets", [])

        if targets:
            FeedTarget.objects.bulk_create(
                [FeedTarget(event=event, **target) for target in targets]
            )
