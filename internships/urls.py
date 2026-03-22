from django.urls import path

from .views import ListCreateInternshipView, ToggleInternshipActiveView, CreateInternshipOfferView, ListInternshipOfferView, ListInternshipApplicationsView, CreateInternshipApplication, UploadApplicationResumeView, AcceptInternshipApplicationView, RejectInternshipApplicationView, AcceptInternshipOfferView, RejectInternshipOfferView, RetrieveUpdateDestroyMentorshipView, RetrieveInternshipOfferView, RetrieveInternshipApplicationView, RetrieveInternshipEngagementView, WithdrawInternshipApplicationView, WithdrawInternshipOfferView, ListInternshipEngagementsView

urlpatterns = [
    path('', ListCreateInternshipView.as_view(), name='list-create-internships'),
    path('/<str:sqid>', RetrieveUpdateDestroyMentorshipView.as_view(), name='retrieve-update-destroy-internships'),
    path('/<str:sqid>/toggle-active', ToggleInternshipActiveView.as_view(), name='toggle-internship-active'),
    
    path('/offer', CreateInternshipOfferView.as_view(), name='create-internship-offers'),
    path('/offers', ListInternshipOfferView.as_view(), name='list-internship-offers'),
    path('/offers/<str:sqid>', RetrieveInternshipOfferView.as_view(), name='retrieve-internship-offers'),
    path('/offers/<str:offer_id>/accept', AcceptInternshipOfferView.as_view(), name='accept-internship-offer'),
    path('/offers/<str:offer_id>/reject', RejectInternshipOfferView.as_view(), name='reject-internship-offer'),
    path('/offers/<str:offer_id>/withdraw', WithdrawInternshipOfferView.as_view(), name='withdraw-internship-offer'),
    
    path('/application', CreateInternshipApplication.as_view(), name='create-internship-application'),
    path('/applications', ListInternshipApplicationsView.as_view(), name='list-create-internship-applications'),
    path('/applications/<str:sqid>', RetrieveInternshipApplicationView.as_view(), name='retrieve-internship-application'),
    path('/upload-resume', UploadApplicationResumeView.as_view(), name='upload-application-resume'),
    path('/applications/<str:application_id>/accept', AcceptInternshipApplicationView.as_view(), name='accept-internship-application'),
    path('/applications/<str:application_id>/reject', RejectInternshipApplicationView.as_view(), name='reject-internship-application'),
    path('/applications/<str:application_id>/withdraw', WithdrawInternshipApplicationView.as_view(), name='withdraw-internship-application'),
    
    path('/engagements', ListInternshipEngagementsView.as_view(), name='list-internship-engagements'),
    path('/engagements/<int:pk>', RetrieveInternshipEngagementView.as_view(), name='retrieve-internship-engagement'),
]
    