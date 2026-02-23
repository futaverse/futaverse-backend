from django.db.models import F
from django.db import transaction

from events.models import Event, Ticket, TicketPurchase
from events.services import EventService

from logging import getLogger
logger = getLogger(__name__)

def handle_charge_success(data):
    print("Handling charge success webhook...")
    reference = data.get("reference")
    
    try:
        with transaction.atomic():
            ticket_purchase = TicketPurchase.objects.select_for_update().select_related('ticket', 'ticket__event', 'ticket__event__creator').get(ticket_uid=reference)
            
            if ticket_purchase.is_paid:
                logger.info(f"Purchase {reference} already processed. Skipping.")
                return
            
            ticket_purchase.is_paid = True
            ticket_purchase.save()

            ticket = ticket_purchase.ticket
            event = ticket.event
            
            Ticket.objects.filter(id=ticket.id).update(quantity_sold=F('quantity_sold') + 1)
        
        if event.mode in [Event.Mode.VIRTUAL, Event.Mode.HYBRID]:
            EventService.sync_to_calendar(event)
        
        EventService.send_ticket_email(ticket_purchase)
                
    except TicketPurchase.DoesNotExist:
        logger.error(f"Purchase not found for reference: {reference}")
    except Exception as e:
        logger.error(f"Error processing webhook for {reference}: {str(e)}")