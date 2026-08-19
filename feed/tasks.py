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
    event_type, related_object_id, related_model, data, audience="public", score=0
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

    ENTITY_TYPE_MAP = {
        "internship": "internship",
        "mentorship": "mentorship",
        "event": "event",
        "internship_engagement": "internship_engagement",
        "mentorship_engagement": "mentorship_engagement",
        "post": "engagement_post",
    }

    data = {**data}

    data["type"] = ENTITY_TYPE_MAP.get(related_model)
    data["sqid"] = related_object.sqid

    if related_model == "post":
        user = related_object.author
        data["author"] = {
            "sqid": user.sqid,
            "full_name": user.full_name,
        }
    else:
        if related_model == "event":
            alumnus = related_object.creator
        else:
            alumnus = related_object.alumnus
        data["alumni"] = {
            "sqid": alumnus.sqid,
            "full_name": alumnus.full_name,
        }

    with transaction.atomic():
        event = FeedEvent.objects.create(
            event_type=event_type, data=data, audience=audience, score=score
        )

        targets = getattr(related_object, "feed_targets", [])

        if targets:
            FeedTarget.objects.bulk_create(
                [FeedTarget(event=event, **target) for target in targets]
            )
