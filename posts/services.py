from .models import Post
from feed.tasks import create_feed_event_task
from feed.models import FeedEvent

DEFAULT_TEXT = {
    'engagement_started': "I'm excited to share that I've started a new {engagement_type} at {company}!",
    'milestone': "Here's an update on my journey at {company}.",
}

def share_engagement(user, engagement, custom_text=None):
    default = DEFAULT_TEXT['engagement_started'].format(
        engagement_type=engagement.type,
        company=engagement.company_name,
    )

    post = Post.objects.create(
        author=user,
        post_type=Post.PostType.ENGAGEMENT_STARTED,
        content=custom_text or default,
        related_object=engagement,
    )

    create_feed_event_task.delay(
        event_type=FeedEvent.EventType.ENGAGEMENT_STARTED,
        related_object_id=post.id,
        related_model='post',
        audience=FeedEvent.Audience.PUBLIC,
        data={
            'post_id':         post.sqid,
            'student_name':    user.profile.full_name,
            'content':         post.content,
            'company':         engagement.company_name,
            'engagement_type': engagement.type,
        }
    )

    return post