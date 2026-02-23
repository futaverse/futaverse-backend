from django.shortcuts import get_object_or_404

from rest_framework.exceptions import ValidationError
from .models import InternshipOffer, InternshipStatus, InternshipApplication

class OfferValidationMixin:
    def get_offer(self) -> InternshipOffer:
        offer_id = self.kwargs.get('offer_id')
        
        if not offer_id:
            raise ValidationError({"detail": "Offer ID is required."})
        
        offer = get_object_or_404(InternshipOffer.objects.all().select_related("internship", "student", "internship__alumnus"), pk=offer_id)
        
        if offer.status != InternshipStatus.PENDING:
            raise ValidationError({"detail": f"Offer has already been {offer.status}."})
    
        if not offer.internship.is_active:
                raise ValidationError({"detail": "internship is not active."})
            
        return offer
    
class ApplicationValidationMixin:
    def get_application(self) -> InternshipApplication:
        application_id = self.kwargs.get('application_id')
        
        if not application_id:
            raise ValidationError({"detail": "application ID is required."})
        
        application = get_object_or_404(InternshipApplication.objects.all().select_related("internship", "student", "internship__alumnus"), pk=application_id)
        
        if not application.internship.is_active:
            raise ValidationError({"detail": "internship is not active."})
        
        if application.status != InternshipStatus.PENDING:
            raise ValidationError({"detail": f"Application has already been {application.status}."})
    
        return application