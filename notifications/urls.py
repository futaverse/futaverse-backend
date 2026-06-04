from .views import ListNotificationsView, MarkNotificationAsReadView, MarkAllNotificationsAsReadView, DeleteNotificationView

from django.urls import path

urlpatterns = [
    path('', ListNotificationsView.as_view(), name='list-notifications'),
    path('/mark-read/<slug:sqid>', MarkNotificationAsReadView.as_view(), name='mark-notification-read'),
    path('/mark-all-read', MarkAllNotificationsAsReadView.as_view(), name='mark-all-notifications-read'),
    path('/delete/<slug:sqid>', DeleteNotificationView.as_view(), name='delete-notification'),        
]