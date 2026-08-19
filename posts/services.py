from django.db import transaction
from django_q.tasks import async_task

from engagements.models import Engagement
from engagements.services import (
    default_completion_text,
    default_share_text,
    feed_event_type,
    get_engagement_post_context,
)
from feed.models import FeedEvent

from .models import Post


@transaction.atomic()
def share_engagement(user, engagement, custom_text=None):
    context = get_engagement_post_context(engagement)
    default_text = default_share_text(engagement)

    post = Post.objects.create(
        author=user,
        post_type=Post.PostType.ENGAGEMENT_STARTED,
        content=custom_text or default_text,
        related_object=engagement,
    )

    transaction.on_commit(
        lambda: async_task(
            "feed.tasks.create_feed_event_task",
            event_type=feed_event_type(engagement),
            related_object_id=post.id,
            related_model="post",
            audience=FeedEvent.Audience.PUBLIC,
            data={"content": post.content, "engagement": context},
        )
    )

    return post


@transaction.atomic()
def share_engagement_completion(user, engagement, custom_text=None):
    context = get_engagement_post_context(engagement)
    default_text = default_completion_text(engagement)

    post = Post.objects.create(
        author=user,
        post_type=Post.PostType.ENGAGEMENT_COMPLETED,
        content=custom_text or default_text,
        related_object=engagement,
    )

    if engagement.engagement_type == Engagement.EngagementType.INTERNSHIP:
        completed_event_type = FeedEvent.EventType.INTERNSHIP_COMPLETED
    else:
        completed_event_type = FeedEvent.EventType.MENTORSHIP_COMPLETED

    transaction.on_commit(
        lambda: async_task(
            "feed.tasks.create_feed_event_task",
            event_type=completed_event_type,
            related_object_id=post.id,
            related_model="post",
            audience=FeedEvent.Audience.PUBLIC,
            data={"content": post.content, "engagement": context},
        )
    )

    return post
