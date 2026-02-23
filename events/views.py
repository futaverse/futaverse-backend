from django.db import transaction
from django.db.models import F
from django.core.cache import cache

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from .serializers import EventSerializer, CreateTicketSerializer, TicketPurchaseSerializer, UpdateEventSerializer, ListEventSerializer, UpdateEventModeSerializer, ListTicketPurchaseSerializer
from .models import Event, VirtualMeeting, Ticket, TicketPurchase
from .services import EventService, GoogleCalendarService, get_user_credentials, GoogleAuthRequired

from futaverse.utils.email_service import BrevoEmailService
# from futaverse.permissions import 
from payments.requests import initialize_transaction

import uuid
import logging

mailer = BrevoEmailService()
logger = logging.getLogger(__name__)

@extend_schema(tags=['Events'], summary="Create an event")
class CreateEventView(generics.CreateAPIView):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        
        validated_data = serializer.validated_data
        
        mode = validated_data.get("mode")
        redirect_after_auth = validated_data.pop("redirect_after_auth", None)
        platform = validated_data.pop("platform", None)
        
        event: Event = serializer.save(creator=user, **validated_data)
        
        if mode in [Event.Mode.VIRTUAL, Event.Mode.HYBRID]:
            try:
                credentials = get_user_credentials(user, redirect_after_auth)
                print(credentials)
                
            except GoogleAuthRequired as e:
                raise PermissionDenied({
                    "detail": "Authenticate with Google",
                    "error": "AUTH_REQUIRED",
                    "auth_url": e.auth_url
                })
                            
            service = GoogleCalendarService(credentials)
            
            if platform == VirtualMeeting.Platform.GOOGLE_MEET:
                room_name = None
                google_event = service.create_event(event, [user.email])
                join_url = google_event.get('hangoutLink')
                external_calendar_event_id = google_event.get('id')
                
            if platform == VirtualMeeting.Platform.JITSI:
                room_name = f"App-{uuid.uuid4().hex}"
                join_url = f"https://meet.jit.si/{room_name}"
                google_event = service.create_event(event, [user.email], manual_join_url=join_url)
                external_calendar_event_id = google_event.get('id')
                
            VirtualMeeting.objects.create(event=event, platform=platform, join_url=join_url, external_calendar_event_id=external_calendar_event_id, room_name=room_name)
            
@extend_schema(tags=['Events'], summary="Add ticket for an event")
class CreateTicketView(generics.CreateAPIView):
    serializer_class = CreateTicketSerializer
            
@extend_schema(tags=['Events'], summary="Register for an event")
class CreateTicketPurchaseView(generics.CreateAPIView):
    serializer_class = TicketPurchaseSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        create_response = self.perform_create(serializer)
        
        if create_response:
            return Response({
                "checkout_url": create_response,
                "message": "Payment required to complete registration"
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @transaction.atomic
    def perform_create(self, serializer):
        #TODO: Handle when action is not performed by user
        
        user = self.request.user
        validated_data = serializer.validated_data
        ticket: Ticket = validated_data.get("ticket")
        event = ticket.event
        
        ticket_uid = uuid.uuid4().hex 
        
        is_free = ticket.sales_price == 0 or ticket.type == Ticket.Type.DEFAULT
        
        ticket_purchase = TicketPurchase.objects.create(user=user, ticket=ticket, is_paid=is_free, ticket_uid=ticket_uid, email=user.email)
             
        if is_free:
            Ticket.objects.filter(id=ticket.id).update(quantity_sold=F('quantity_sold') + 1)
            
            if event.mode in [Event.Mode.VIRTUAL, Event.Mode.HYBRID]:
                EventService.sync_to_calendar(event)
                
            EventService.send_ticket_email(ticket_purchase)
            
            return None
            
        else:
            authorization_url = initialize_transaction({
                "amount": int(ticket.sales_price * 100), 
                "email": user.email,
                "reference": str(ticket_uid)
            })
            
            return authorization_url

@extend_schema(tags=['Events'], summary="Update an event")     
class UpdateEventView(generics.UpdateAPIView):
    serializer_class = UpdateEventSerializer
    queryset = Event.objects.all()
    lookup_field = 'sqid'
    http_method_names = ['patch']
    
    def perform_update(self, serializer):
        instance: Event = self.get_object()
        
        lock_key = f"info_update_{instance.sqid}"
        if cache.get(lock_key):
            return Response({"detail": "Request already in progress."}, status=409)
        cache.set(lock_key, True, timeout=5) 
        
        old_data = {
            'date': instance.date.strftime('%B %d, %Y'),
            'time': instance.start_time.strftime('%I:%M %p')
        }
        
        validated_data: dict = serializer.validated_data
        
        time_fields = ['date', 'start_time', 'duration_mins']
        time_changed = any(field in validated_data and validated_data[field] != getattr(instance, field) for field in time_fields)
        
        with transaction.atomic():
            event = serializer.save()
        
        if hasattr(event, 'virtual_meeting'):
            try:
                user = self.request.user
                redirect_after_auth = validated_data.get("redirect_after_auth", None)
                
                credentials = get_user_credentials(user, redirect_after_auth)
                
            except GoogleAuthRequired as e:
                raise PermissionDenied({
                    "detail": "Authenticate with Google",
                    "error": "AUTH_REQUIRED",
                    "auth_url": e.auth_url
                })
            
            is_jitsi = event.virtual_meeting.platform == VirtualMeeting.Platform.JITSI           
            service = GoogleCalendarService(credentials)
            service.update_event_details(event, validated_data, manual_join_url=event.virtual_meeting.join_url if is_jitsi else None)
        
        if time_changed:
            EventService.send_event_update_emails(event, old_data)

@extend_schema(tags=['Events'], summary="List user's hosted events")             
class ListEventsView(generics.ListAPIView):
    serializer_class = ListEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Event.objects.filter(creator=user).prefetch_related('tickets', 'virtual_meeting').select_related('creator')
    
@extend_schema(tags=['Events'], summary="Get event's details")
class RetrieveEventView(generics.RetrieveAPIView):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'sqid'
    
    def get_queryset(self):
        user = self.request.user
        return Event.objects.filter(creator=user).prefetch_related('tickets', 'virtual_meeting').select_related('creator')
    
@extend_schema(tags=['Events'], summary="Update event mode")
class UpdateEventModeView(generics.UpdateAPIView):
    serializer_class = UpdateEventModeSerializer
    queryset = Event.objects.all()
    lookup_field = 'sqid'
    http_method_names = ['patch']
    
    def perform_update(self, serializer):
        instance = self.get_object()
        
        lock_key = f"mode_update_{instance.sqid}"
        if cache.get(lock_key):
            return Response({"detail": "Request already in progress."}, status=409)
        cache.set(lock_key, True, timeout=10) 
        
        old_mode = instance.mode
        new_mode = serializer.validated_data.get('mode')
        
        platform = serializer.validated_data.get('platform')
        venue = serializer.validated_data.get('venue')
        
        with transaction.atomic():
            event = serializer.save()

        if old_mode != new_mode:
            EventService.reconcile_mode_change(event, old_mode, new_mode, self.request.user, platform=platform, venue=venue)
            EventService.send_mode_change_email(event, old_mode, new_mode)
            
@extend_schema(tags=['Events'], summary="List user's purchased tickets")
class ListPurchasedTicketsView(generics.ListAPIView):
    serializer_class = ListTicketPurchaseSerializer
    permission_classes = [IsAuthenticated]
    # queryset = TicketPurchase.objects.all()
    
    def get_queryset(self):
        user = self.request.user
        return TicketPurchase.objects.filter(user=user).select_related('ticket', 'ticket__event').order_by('-created_at')
    