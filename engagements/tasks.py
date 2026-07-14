from django.utils import timezone

from datetime import timedelta
from django.conf import settings
from django_q.tasks import async_task, logger, schedule, Schedule

from engagements.models import BaseEngagement

from futaverse.lib import MODELS
from engagements.plugins import get_engagement_plugin

def auto_acknowledge_engagement(engagement_sqid, engagement_type):
    model = MODELS.get(engagement_type)
    
    if not model:
        raise ValueError(f"Invalid engagement type: {engagement_type}")
    
    try:
        engagement = model.objects.get(sqid=engagement_sqid)
    except model.DoesNotExist:
        return  
    
    engagement.refresh_from_db()
    
    if engagement.status == BaseEngagement.EngagementStatus.COMPLETED:
        engagement.update_status(BaseEngagement.EngagementStatus.ACKNOWLEDGED)
        
        async_task(
            "notifications.tasks.send_notifications_task",
            user_ids=[engagement.student.user.id],
            title='Engagement Auto-Acknowledged',
            content=f'Your {engagement_type.replace("_engagement", "")} with {engagement.alumnus.full_name} has been automatically acknowledged due to getting no response from your end.'
        )


def schedule_auto_ackowledgement_task(engagement_data):
    engagement_type = engagement_data.get("engagement_type")
    sqid = engagement_data.get("sqid")
    engagement_plugin = get_engagement_plugin(engagement_type)
    domain = engagement_plugin.get("domain")
    
    model = MODELS.get(engagement_type)
    
    if not model:
        raise ValueError(f"Invalid engagement type: {engagement_type}")
    
    try:
        engagement = model.objects.get(sqid=sqid)
    except model.DoesNotExist:
        logger.warning(f"Engagement with sqid {sqid} does not exist.")
        return
    
    engagement.refresh_from_db()
    student_id = engagement.student.user.id
    alumnus_name = engagement.alumnus.full_name
    
    async_task(
        "notifications.tasks.send_notifications_task",
        user_ids=[student_id],
        title=f'{domain} Completed',
        content=f'Your {engagement_plugin.get("domain")} with {alumnus_name} has been marked as completed.'
    )
    
    schedule(
        "notifications.tasks.send_notifications_task",
        user_ids=[student_id],
        title=f'Acknowledgement Reminder for {domain}',
        content=f'Please acknowledge your {domain} with {alumnus_name} in 24 hours, else it will be automatically acknowledged.',
        schedule_type=Schedule.ONCE,
        next_run=timezone.now() + timedelta(hours=settings.ENGAGEMENT_ACKNOWLEDGEMENT_REMINDER_HOURS),
        name=f'acknowledgement_reminder_{domain}_{sqid}'
    )
    
    schedule(
        "engagements.tasks.auto_acknowledge_engagement",
        engagement_sqid=sqid,
        engagement_type=engagement_type,
        schedule_type=Schedule.ONCE,
        next_run=timezone.now() + timedelta(hours=settings.ENGAGEMENT_AUTO_ACKNOWLEDGE_HOURS),
        name=f'auto_acknowledge_engagement_{domain}_{sqid}'
    )