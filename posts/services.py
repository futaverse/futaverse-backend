from django.db import transaction
from django_q.tasks import async_task

from .models import Post
from feed.models import FeedEvent

from engagements.plugins import get_engagement_plugin

@transaction.atomic()
def share_engagement(user, engagement, custom_text=None):
    context = getattr(engagement, 'post_context', {})
    plugin = get_engagement_plugin(engagement.__class__)
    
    if not plugin:
        raise ValueError(f"Unknown engagement type")
    
    default_text = plugin.get("default_text")(context)
    
    post = Post.objects.create(
        author=user,
        post_type=Post.PostType.ENGAGEMENT_STARTED,
        content=custom_text or default_text,
        related_object=engagement,
    )

    transaction.on_commit(lambda: async_task("feed.tasks.create_feed_event_task",
        event_type=plugin.get("feed_event"),
        related_object_id=engagement.id,
        related_model= plugin.get("model"),
        audience=FeedEvent.Audience.PUBLIC,
        data={
            **context,
        }
    ))

    return post

@transaction.atomic()
def share_engagement_completion(user, engagement, custom_text=None):
    context = getattr(engagement, 'post_context', {})
    plugin = get_engagement_plugin(engagement.__class__)
    
    if not plugin:
        raise ValueError(f"Unknown engagement type")
    
    default_text = plugin.get("default_completion_text")(context)
    
    post = Post.objects.create(
        author=user,
        post_type=Post.PostType.ENGAGEMENT_COMPLETED,
        content=custom_text or default_text,
        related_object=engagement,
    )

    transaction.on_commit(lambda: async_task("feed.tasks.create_feed_event_task",
        event_type=plugin.get("feed_event"),
        related_object_id=engagement.id,
        related_model= plugin.get("model"),
        audience=FeedEvent.Audience.PUBLIC,
        data={
            **context,
        }
    ))

    return post