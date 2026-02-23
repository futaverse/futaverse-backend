from django.urls import path

from .views import ListCreateMentorshipView, RetrieveUpdateDestroyMentorshipView, CreateMentorshipOfferView, ListMentorshipOfferView, RetrieveMentorshipOfferView, AcceptOfferView, RejectOfferView, WithdrawOfferView, CreateMentorshipApplicationView, ListMentorshipApplicationsView, RetrieveMentorshipApplicationView, AcceptApplicationView, RejectApplicationView, WithdrawApplicationView, ToggleMentorshipActiveView, ListMentorshipEngagementsView, RetrieveMentorshipEngagementView

urlpatterns = [
    path('', ListCreateMentorshipView.as_view(), name='list-create-mentorships'),
    path('/<int:pk>', RetrieveUpdateDestroyMentorshipView.as_view(), name='retrieve-update-destroy-mentorships'),
    path('/<int:pk>/toggle-active', ToggleMentorshipActiveView.as_view(), name='toggle-mentorship-active'),
    
    path('/offer', CreateMentorshipOfferView.as_view(), name='create-mentorship-offers'),
    path('/offers', ListMentorshipOfferView.as_view(), name='list-mentorship-offers'),
    path('/offers/<int:pk>', RetrieveMentorshipOfferView.as_view(), name='retrieve-mentorship-offers'),
    path('/offers/<int:offer_id>/accept', AcceptOfferView.as_view(), name='accept-mentorship-offer'),
    path('/offers/<int:offer_id>/reject', RejectOfferView.as_view(), name='reject-mentorship-offer'),
    path('/offers/<int:offer_id>/withdraw', WithdrawOfferView.as_view(), name='withdraw-mentorship-offer'),
    
    path('/application', CreateMentorshipApplicationView.as_view(), name='create-mentorship-application'),
    path('/applications', ListMentorshipApplicationsView.as_view(), name='list-mentorship-applications'),
    path('/applications/<int:pk>', RetrieveMentorshipApplicationView.as_view(), name='retrieve-mentorship-application'),
    path('/applications/<int:application_id>/accept', AcceptApplicationView.as_view(), name='accept-mentorship-application'),
    path('/applications/<int:application_id>/reject', RejectApplicationView.as_view(), name='reject-mentorship-application'),
    path('/applications/<int:application_id>/withdraw', WithdrawApplicationView.as_view(), name='withdraw-mentorship-application'),
    
    path('/engagements', ListMentorshipEngagementsView.as_view(), name='list-mentorship-engagements'),
    path('/engagements/<int:pk>', RetrieveMentorshipEngagementView.as_view(), name='retrieve-mentorship-engagement'),
]