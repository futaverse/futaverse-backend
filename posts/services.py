from .models import Post
from feed.tasks import create_feed_event_task
from feed.models import FeedEvent

def humanize_list(items):
    if len(items) == 1:
        return items[0]
    return ', '.join(items[:-1]) + f' and {items[-1]}'

engagement_handlers = {
    "internship": lambda context: {
        "default_text": (
            f"I'm excited to share that I've just started a new internship "
            f"at {context['company']} as a {context['title']}!"
        ),
        "feed_event": FeedEvent.EventType.INTERNSHIP_STARTED,
        "model": "internship_engagement",
    },
    
    "mentorship": lambda context: {
        "default_text": (
            f"Excited to share that I've just started a mentorship journey in "
            f"{context['category']} with a FUTA alumnus! Looking forward to growing "
            f"in {humanize_list(context['focus_areas'])}."
        ),
        "feed_event": FeedEvent.EventType.MENTORSHIP_STARTED,
        "model": 'mentorship_engagement',
    },
}

def share_engagement(user, engagement, custom_text=None):
    context = engagement.post_context
    engagement_type = context['type']
    
    handler = engagement_handlers.get(engagement_type, None)
    if not handler:
        raise ValueError(f"Unknown engagement type: {engagement_type}")
    
    defaults = handler(context)
    default_text = defaults.get("default_text")
    
    post = Post.objects.create(
        author=user,
        post_type=Post.PostType.ENGAGEMENT_STARTED,
        content=custom_text or default_text,
        related_object=engagement,
    )

    create_feed_event_task.delay(
        event_type=defaults.get("feed_event"),
        related_object_id=post.id,
        related_model= defaults.get("model"),
        audience=FeedEvent.Audience.PUBLIC,
        data={
            **context,
        }
    )

    return post