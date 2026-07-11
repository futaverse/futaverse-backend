from django.urls import path

from engagements.helpers import generate_engagement_urls

from .views.applications import (
    ListMentorshipApplicationsView,
    CreateMentorshipApplicationView,
    AcceptMentorshipApplicationView,
    RejectMentorshipApplicationView,
    WithdrawMentorshipApplicationView,
    RetrieveMentorshipApplicationView,
)

from .views.offers import (
    ListMentorshipOfferView,
    CreateMentorshipOfferView,
    AcceptMentorshipOfferView,
    RejectMentorshipOfferView,
    WithdrawMentorshipOfferView,
    RetrieveMentorshipOfferView,
)

from .views.mentorships import (
    ListCreateMentorshipView,
    ToggleMentorshipActiveView,
    RetrieveMentorshipEngagementView,
    ListMentorshipEngagementsView,
    RetrieveUpdateDestroyMentorshipView,
    MentorshipChoicesView,
    MarkMentorshipAcknowledgedView,
    MarkMentorshipCompletedView,
)

urlpatterns = generate_engagement_urls(
    prefix="mentorship",
    entity_views={
        "list_create": ListCreateMentorshipView,
        "rud": RetrieveUpdateDestroyMentorshipView,
        "toggle_active": ToggleMentorshipActiveView,
    },
    application_views={
        "create": CreateMentorshipApplicationView,
        "list": ListMentorshipApplicationsView,
        "retrieve": RetrieveMentorshipApplicationView,
        "accept": AcceptMentorshipApplicationView,
        "reject": RejectMentorshipApplicationView,
        "withdraw": WithdrawMentorshipApplicationView,
    },
    offer_views={
        "create": CreateMentorshipOfferView,
        "list": ListMentorshipOfferView,
        "retrieve": RetrieveMentorshipOfferView,
        "accept": AcceptMentorshipOfferView,
        "reject": RejectMentorshipOfferView,
        "withdraw": WithdrawMentorshipOfferView,
    },
    engagement_views={
        "list": ListMentorshipEngagementsView,
        "retrieve": RetrieveMentorshipEngagementView,
        "completed": MarkMentorshipCompletedView,
        "acknowledged": MarkMentorshipAcknowledgedView,
    },
    extra=[
        path('/choices', MentorshipChoicesView.as_view(), name='mentorship-choices'),
    ],
)
