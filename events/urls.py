from django.urls import path
from .views import CreateEventView, CreateTicketView, CreateTicketPurchaseView, UpdateEventView, ListEventsView, RetrieveEventView, UpdateEventModeView, ListPurchasedTicketsView

urlpatterns = [
    path('', CreateEventView.as_view(), name='create-event'),
    
    path('ticket', CreateTicketView.as_view(), name='create-ticket'),
    path('register', CreateTicketPurchaseView.as_view(), name='create-ticket-purchase'),
    
    path('list', ListEventsView.as_view(), name='list-events'),
    path('tickets', ListPurchasedTicketsView.as_view(), name='list-purchased-tickets'),
    
    path('update/<slug:sqid>', UpdateEventView.as_view(), name='update-event'),
    path('update/<slug:sqid>/mode', UpdateEventModeView.as_view(), name='update-event-mode'),
    
    path('<slug:sqid>', RetrieveEventView.as_view(), name='retrieve-event'),
]