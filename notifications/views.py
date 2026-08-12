
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Notification
from .serializers import NotificationSerializer

@extend_schema(tags=['Notifications'], summary="List notifications for the logged in user")
class ListNotificationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.none()
    
    def get_queryset(self):
        user = self.request.user
        
        return Notification.objects.filter(user=user).order_by('-created_at')
    
@extend_schema(tags=['Notifications'], summary="Mark a notification as read")
class MarkNotificationAsReadView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    http_method_names = ['patch']
    lookup_field = 'sqid'
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        notification = serializer.instance
        
        notification.mark_as_read()

@extend_schema(tags=['Notifications'], summary="Delete a notification")
class DeleteNotificationView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    lookup_field = 'sqid'
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
@extend_schema(tags=['Notifications'], summary="Mark all notifications as read")
class MarkAllNotificationsAsReadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None
    http_method_names = ['patch']
    
    def patch(self, request):
        user = request.user
        
        Notification.objects.filter(user=user, is_read=False).update(is_read=True, read_at=timezone.now())
        
        return Response({"detail": "All notifications marked as read."}, status=status.HTTP_200_OK)