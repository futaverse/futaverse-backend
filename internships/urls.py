from django.urls import path

from .views import ListCreateInternshipView, ToggleInternshipActiveView, CreateInternshipOfferView, ListInternshipOfferView, ListInternshipApplicationsView, CreateInternshipApplication, UploadApplicationResumeView, AcceptInternshipApplicationView, RejectInternshipApplicationView, AcceptInternshipOfferView, RejectInternshipOfferView, RetrieveUpdateDestroyMentorshipView, RetrieveInternshipOfferView, RetrieveInternshipApplicationView, RetrieveInternshipEngagementView, WithdrawInternshipApplicationView, WithdrawInternshipOfferView, ListInternshipEngagementsView

urlpatterns = [
    path('/application', CreateInternshipApplication.as_view(), name='create-internship-application'),
    path('/applications', ListInternshipApplicationsView.as_view(), name='list-create-internship-applications'),
    path('/offer', CreateInternshipOfferView.as_view(), name='create-internship-offers'),
    path('/offers', ListInternshipOfferView.as_view(), name='list-internship-offers'),
    path('/engagements', ListInternshipEngagementsView.as_view(), name='list-internship-engagements'),
    path('/upload-resume', UploadApplicationResumeView.as_view(), name='upload-application-resume'),
    
    path('/offers/<slug:sqid>', RetrieveInternshipOfferView.as_view(), name='retrieve-internship-offers'),
    path('/offers/<slug:offer_id>/accept', AcceptInternshipOfferView.as_view(), name='accept-internship-offer'),
    path('/offers/<slug:offer_id>/reject', RejectInternshipOfferView.as_view(), name='reject-internship-offer'),
    path('/offers/<slug:offer_id>/withdraw', WithdrawInternshipOfferView.as_view(), name='withdraw-internship-offer'),
   
    path('/applications/<slug:sqid>', RetrieveInternshipApplicationView.as_view(), name='retrieve-internship-application'),
    path('/applications/<slug:application_id>/accept', AcceptInternshipApplicationView.as_view(), name='accept-internship-application'),
    path('/applications/<slug:application_id>/reject', RejectInternshipApplicationView.as_view(), name='reject-internship-application'),
    path('/applications/<slug:application_id>/withdraw', WithdrawInternshipApplicationView.as_view(), name='withdraw-internship-application'),
    
    path('/engagements/<slug:sqid>', RetrieveInternshipEngagementView.as_view(), name='retrieve-internship-engagement'),
    
    path('', ListCreateInternshipView.as_view(), name='list-create-internships'),
    path('/<slug:sqid>', RetrieveUpdateDestroyMentorshipView.as_view(), name='retrieve-update-destroy-internships'),
    path('/<slug:sqid>/toggle-active', ToggleInternshipActiveView.as_view(), name='toggle-internship-active'),
]
    