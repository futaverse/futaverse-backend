from django.db import transaction
from django_q.tasks import async_task

from .models import Post
from feed.tasks import create_feed_event_task
from feed.models import FeedEvent

from .lib import POST_PLUGINS

@transaction.atomic()
def share_engagement(user, engagement, custom_text=None):
    context = getattr(engagement, 'post_context', {})
    plugin = POST_PLUGINS.get(engagement.__class__)
    
    if not plugin:
        raise ValueError(f"Unknown engagement type")
    
    default_text = plugin.get("default_text")(context)
    
    post = Post.objects.create(
        author=user,
        post_type=Post.PostType.ENGAGEMENT_STARTED,
        content=custom_text or default_text,
        related_object=engagement,
    )

    async_task(create_feed_event_task,
        event_type=plugin.get("feed_event"),
        related_object_id=engagement.id,
        related_model= plugin.get("model"),
        audience=FeedEvent.Audience.PUBLIC,
        data={
            **context,
        }
    )

    return post