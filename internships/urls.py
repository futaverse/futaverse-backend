from engagements.helpers import generate_engagement_urls

from .views.applications import (
    ListInternshipApplicationsView,
    CreateInternshipApplicationView,
    AcceptInternshipApplicationView,
    RejectInternshipApplicationView,
    WithdrawInternshipApplicationView,
    RetrieveInternshipApplicationView,
)
 
from .views.offers import (
    ListInternshipOfferView,
    CreateInternshipOfferView,
    AcceptInternshipOfferView,
    RejectInternshipOfferView,
    WithdrawInternshipOfferView,
    RetrieveInternshipOfferView,
)

from .views.internships import (
    ListCreateInternshipView,
    ToggleInternshipActiveView,
    RetrieveInternshipEngagementView,
    ListInternshipEngagementsView,
    InternshipDetailView,
    MarkInternshipAcknowledgedView,
    MarkInternshipCompletedView,
)

urlpatterns = generate_engagement_urls(
    prefix="internship",
    entity_views={
        "list_create": ListCreateInternshipView,
        "rud": InternshipDetailView,
        "toggle_active": ToggleInternshipActiveView,
    },
    application_views={
        "create": CreateInternshipApplicationView,
        "list": ListInternshipApplicationsView,
        "retrieve": RetrieveInternshipApplicationView,
        "accept": AcceptInternshipApplicationView,
        "reject": RejectInternshipApplicationView,
        "withdraw": WithdrawInternshipApplicationView,
    },
    offer_views={
        "create": CreateInternshipOfferView,
        "list": ListInternshipOfferView,
        "retrieve": RetrieveInternshipOfferView,
        "accept": AcceptInternshipOfferView,
        "reject": RejectInternshipOfferView,
        "withdraw": WithdrawInternshipOfferView,
    },
    engagement_views={
        "list": ListInternshipEngagementsView,
        "retrieve": RetrieveInternshipEngagementView,
        "completed": MarkInternshipCompletedView,
        "acknowledged": MarkInternshipAcknowledgedView,
    },
)
