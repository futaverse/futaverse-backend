from django.db import transaction
from django_q.tasks import async_task

from .models import Post
from feed.models import FeedEvent

from engagements.services import (
    get_engagement_post_context,
    default_share_text,
    default_completion_text,
    feed_event_type,
)


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

    transaction.on_commit(lambda: async_task("feed.tasks.create_feed_event_task",
        event_type=feed_event_type(engagement),
        related_object_id=engagement.id,
        related_model=engagement.engagement_type,
        audience=FeedEvent.Audience.PUBLIC,
        data={**context},
    ))

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

    transaction.on_commit(lambda: async_task("feed.tasks.create_feed_event_task",
        event_type=feed_event_type(engagement),
        related_object_id=engagement.id,
        related_model=engagement.engagement_type,
        audience=FeedEvent.Audience.PUBLIC,
        data={**context},
    ))

    return post
