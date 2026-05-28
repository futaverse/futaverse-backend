from django.db import transaction
from django.utils import timezone

from django_eventstream import send_event

from .models import Notification
from .serializers import NotificationSerializer

def emit_notifications(notifications):
    serialized = NotificationSerializer(notifications, many=True).data
    
    for notification, data in zip(notifications, serialized):
        channel = f'user-{notification.user.sqid}'
        new_notifications = Notification.objects.filter(user=notification.user, is_read=False).count()
        
        send_event(channel, event_type='new_notification', data={
            'data': data,
            'new_notifications': new_notifications,
            'type': 'new_notification',
            'timestamp': timezone.now().isoformat(),
        })

def send_notifications_task(user_ids, title, content):
    with transaction.atomic():
        notifications = Notification.objects.bulk_create(
            [Notification(user_id=user_id, title=title, content=content) for user_id in user_ids]
        )
        
        notification_ids = [notification.id for notification in notifications]
        
        full_notifications = list(Notification.objects.filter(id__in=notification_ids).select_related('user'))
        
    transaction.on_commit(lambda: emit_notifications(full_notifications)) 