from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import TicketPurchase, Event, VirtualMeeting
from core.models import User

from logging import getLogger
from datetime import timedelta, datetime

from futaverse.utils.email_service import BrevoEmailService
from futaverse.utils.google.views import build_google_auth_url

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

import uuid

logger = getLogger(__name__)
mailer = BrevoEmailService()

class EventService:
    @staticmethod
    def sync_to_calendar(event):
        try:
            virtual_meeting = getattr(event, 'virtual_meeting', None)
            if not virtual_meeting:
                return

            credentials = get_user_credentials(event.creator)
            service = GoogleCalendarService(credentials)

            all_emails = list(TicketPurchase.objects.filter(
                ticket__event=event, 
                is_paid=True
            ).values_list('email', flat=True))
            
            if event.creator.email not in all_emails:
                all_emails.append(event.creator.email)

            service.add_attendee_to_event(
                event_id=virtual_meeting.external_calendar_event_id,
                new_attendee_emails=all_emails
            )
            
        except Exception as e:
            logger.error(f"Calendar sync failed: {e}")

    @staticmethod
    def send_ticket_email(ticket_purchase):
        event: Event = ticket_purchase.ticket.event
        user_name = ticket_purchase.user.get_full_name() if ticket_purchase.user else ticket_purchase.email 
        join_url = getattr(event, 'virtual_meeting', None).join_url if hasattr(event, 'virtual_meeting') else None
        start_datetime = timezone.make_aware(datetime.combine(event.date, event.start_time))
        
        context = {
            'user_name': user_name,
            'event_title': event.title,
            'event_date': start_datetime.strftime('%B %d, %Y at %H:%M %p'),
            'event_location': "Virtual Meeting" if event.mode == "VIRTUAL" else event.venue, # TODO: Add location to event
            'ticket_uid': str(ticket_purchase.ticket_uid),
            'join_url': join_url
        }
        
        html_body = render_to_string('emails/ticket_confirmation.html', context)
        
        mailer.send(
            subject=f"Confirmation: Your Ticket for {event.title}",
            body=html_body,
            recipient=ticket_purchase.email,
            is_html=True
        )
    
    @staticmethod
    def send_event_update_emails(event, old_data):
        attendee_emails = list(TicketPurchase.objects.filter(ticket__event=event, is_paid=True).values_list('email', flat=True).distinct())

        if not attendee_emails:
            return

        context = {
            'event_title': event.title,
            'old_date': old_data['date'],
            'old_time': old_data['time'],
            'new_date': event.date.strftime('%B %d, %Y'),
            'new_time': event.start_time.strftime('%I:%M %p'),
            'event_url': f"https://google.com" #TODO: Change later to actual event URL
        }
        
        html_body = render_to_string('emails/event_schedule_update.html', context)
        
        mailer.send_bulk(
            subject=f"SCHEDULE UPDATE: {event.title}",
            body=html_body,
            recipients=attendee_emails, 
            is_html=True
        )
        
    @staticmethod
    def reconcile_mode_change(event, old_mode, new_mode, user, platform=None, venue=None):
        """
        Handles the technical side effects of changing an event mode.
        """
        print()
        if new_mode in [Event.Mode.VIRTUAL, Event.Mode.HYBRID]:
            if not hasattr(event, 'virtual_meeting'):
                try: 
                    credentials = get_user_credentials(user) # TODO: Add redirect after auth
                    service = GoogleCalendarService(credentials)
                    
                except GoogleAuthRequired as e:
                    raise PermissionDenied({
                        "detail": "Authenticate with Google",
                        "error": "AUTH_REQUIRED",
                        "auth_url": e.auth_url
                    })
                    
                attendee_emails = list(TicketPurchase.objects.filter(ticket__event=event, is_paid=True).values_list('email', flat=True).distinct())
                
                if user.email not in attendee_emails:
                    attendee_emails.append(user.email)
                
                if platform == VirtualMeeting.Platform.GOOGLE_MEET:
                    room_name = None
                    google_event = service.create_event(event, attendee_emails)
                    join_url = google_event.get('hangoutLink')
                    external_calendar_event_id = google_event.get('id')
                    
                if platform == VirtualMeeting.Platform.JITSI:
                    room_name = f"App-{uuid.uuid4().hex}"
                    join_url = f"https://meet.jit.si/{room_name}"
                    google_event = service.create_event(event, attendee_emails, manual_join_url=join_url)
                    external_calendar_event_id = google_event.get('id')
                
                try:
                    with transaction.atomic():
                        VirtualMeeting.objects.create(event=event, platform=platform, join_url=join_url, external_calendar_event_id=external_calendar_event_id, room_name=room_name)
                except Exception as e:  
                    service.delete_event(external_calendar_event_id)
                    logger.error(f"Failed to save VirtualMeeting to DB. Google Event rolled back: {e}")
                    raise

        if new_mode == Event.Mode.PHYSICAL and hasattr(event, 'virtual_meeting'):
            try:
                try: 
                    credentials = get_user_credentials(user) # TODO: Add redirect after auth
                    service = GoogleCalendarService(credentials)
                    
                except GoogleAuthRequired as e:
                    raise PermissionDenied({
                        "detail": "Authenticate with Google",
                        "error": "AUTH_REQUIRED",
                        "auth_url": e.auth_url
                    })
                    
                service.delete_event(event.virtual_meeting.external_calendar_event_id)
            
            except Exception as e:
                logger.error(f"Failed to delete Google Event during mode switch: {e}")
            
            with transaction.atomic(): 
                event.venue = venue
                event.save(update_fields=['venue'])
                event.virtual_meeting.delete()
                
    @staticmethod
    def send_mode_change_email(event, old_mode, new_mode):
        print("Sending mode change email...")
        attendee_emails = list(TicketPurchase.objects.filter(ticket__event=event, is_paid=True).values_list('email', flat=True).distinct())

        if not attendee_emails:
            return

        context = {
            'event_title': event.title,
            'old_mode': old_mode,
            'new_mode': new_mode,
            'venue': event.venue if event.venue else "TBA",
            'platform': event.virtual_meeting.platform if hasattr(event, 'virtual_meeting') else "TBA",
            'event_url': f"https://google.com" #TODO: Change later to actual event URL
        }
        
        html_body = render_to_string('emails/event_mode_change.html', context)
        
        mailer.send_bulk(
            subject=f"Format Change: {event.title}",
            body=html_body,
            recipients=attendee_emails,
            is_html=True
        )
    
class GoogleAuthRequired(Exception):
    def __init__(self, auth_url):
        self.auth_url = auth_url
        
class GoogleCalendarService:
    def __init__(self, credentials):
        self.service = build("calendar", "v3", credentials=credentials)

    def create_event(self, event: Event, attendees_emails, manual_join_url=None):
        
        start_datetime = timezone.make_aware(datetime.combine(event.date, event.start_time))
        end_datetime = start_datetime + timedelta(minutes=event.duration_mins)
        
        body = {
            'summary': event.title,
            'description': f"Join Meeting: {manual_join_url}\n\n{event.description}" if manual_join_url else event.description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': settings.TIME_ZONE,
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': settings.TIME_ZONE,
            },
            'attendees': [{'email': email} for email in attendees_emails],
            
            # Tag the event with our database ID for easy searching later
            'extendedProperties': {
                'private': {
                    'app_event_id': str(event.sqid),
                }
            },
            "conferenceData": {
                'createRequest': {
                    'requestId': f"req-{event.sqid}", 
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            }

        try:
            return self.service.events().insert(
                calendarId='primary',
                body=body,
                conferenceDataVersion=1 if not manual_join_url else 0,
                sendUpdates='all'        
            ).execute()
            
        except HttpError as e:
            logger.error(f"Google Calendar Create Error: {e}")
            raise 
        
    def add_attendee_to_event(self, event_id, new_attendee_emails):
        """
        event_id: The external_calendar_event_id
        new_attendee_emails: List of current + new attendee emails
        """
        try:
            body = {
                'attendees': [{'email': email} for email in new_attendee_emails]
            }

            return self.service.events().patch(
                calendarId='primary',
                eventId=event_id,
                body=body,
                sendUpdates='all'  
            ).execute()
            
        except HttpError as e:
            logger.error(f"Error patching calendar attendees: {e}")
            return None
        
    def update_event_details(self, event: Event, changes, manual_join_url=None):
        body = {}
        
        date_fields = ['date', 'start_time', 'duration_mins']
        time_changed = any(field in changes for field in date_fields)
        
        if time_changed:
            new_date = changes.get('date', event.date)
            new_time = changes.get('start_time', event.start_time)
            new_duration = changes.get('duration_mins', event.duration_mins)
            
            start_dt = timezone.make_aware(datetime.combine(new_date, new_time))
            end_dt = start_dt + timedelta(minutes=new_duration)
            
            body['start'] = {'dateTime': start_dt.isoformat(), 'timeZone': settings.TIME_ZONE}
            body['end'] = {'dateTime': end_dt.isoformat(), 'timeZone': settings.TIME_ZONE}
            
        if 'title' in changes:
            body['summary'] = changes['title']
            
        if 'description' in changes:
            desc = changes['description']
            body['description'] = f"Join Meeting: {manual_join_url}\n\n{desc}" if manual_join_url else desc
            
        if body == {}:
            return None 
        
        try:
            external_id = event.virtual_meeting.external_calendar_event_id
            
            return self.service.events().patch(
                calendarId='primary',
                eventId=external_id,
                body=body,
                conferenceDataVersion=1,
                sendUpdates='all' 
            ).execute()
            
        except HttpError as e:
            logger.error(f"Google Calendar Update Error: {e}")
            raise
        
    def delete_event(self, event_id):
        """
        Deletes an event from the user's primary calendar.
        """
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all' 
            ).execute()
            return True
        
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Google Event {event_id} already deleted or not found.") # Ensures the app doesn't crash if the is already deleted or doesn't exist
                return True
            
            logger.error(f"Google Calendar Delete Error: {e}")
            raise
        
def get_user_credentials(user: User, redirect_after_auth=None):
    creds_data = user.google_credentials
    google_auth_url = build_google_auth_url(user.sqid, redirect_after_auth)
    
    if not creds_data or not creds_data.get('token'):
        print("no creds")
        raise GoogleAuthRequired(google_auth_url)
    
    credentials = Credentials.from_authorized_user_info(creds_data)
    
    if not credentials.expired:
        return credentials

    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            
            user.google_credentials = {
                **creds_data,
                'token': credentials.token,
                'refresh_token': credentials.refresh_token
            }
            user.save(update_fields=['google_credentials'])
            
            return credentials
        
        except Exception as e:
            logger.error(f"Refresh token failed for {user.email}: {e}")
            raise GoogleAuthRequired(google_auth_url)
            
    raise GoogleAuthRequired(google_auth_url)