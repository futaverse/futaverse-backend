from django.shortcuts import get_object_or_404

from rest_framework.exceptions import ValidationError
from .models import MentorshipOffer, MentorshipStatus, MentorshipApplication

class OfferValidationMixin:
    def get_offer(self) -> MentorshipOffer:
        offer_id = self.kwargs.get('offer_id')
        
        if not offer_id:
            raise ValidationError({"detail": "Offer ID is required."})
        
        offer = get_object_or_404(MentorshipOffer.objects.all().select_related("mentorship", "student", "mentorship__alumnus"), pk=offer_id)
        
        if offer.status != MentorshipStatus.PENDING:
            raise ValidationError({"detail": f"Offer has already been {offer.status}."})
    
        if not offer.mentorship.is_active:
                raise ValidationError({"detail": "Mentorship is not active."})
            
        return offer
    
class ApplicationValidationMixin:
    def get_application(self) -> MentorshipApplication:
        application_id = self.kwargs.get('application_id')
        
        if not application_id:
            raise ValidationError({"detail": "application ID is required."})
        
        application = get_object_or_404(MentorshipApplication.objects.all().select_related("mentorship", "student", "mentorship__alumnus"), pk=application_id)
        
        if not application.mentorship.is_active:
            raise ValidationError({"detail": "Mentorship is not active."})
        
        if application.status != MentorshipStatus.PENDING:
            raise ValidationError({"detail": f"Application has already been {application.status}."})
    
        return application