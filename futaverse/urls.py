from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from core.views import UploadUserProfileImageView
from .utils.google.views import google_auth_start, google_auth_callback
from .views import health_check

from core.views import ListStudentResumesView, UploadStudentResumeView, DeleteStudentResumeView

urlpatterns = [
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/raw', SpectacularAPIView.as_view(), name='schema'),

    path('health', health_check, name='health-check'),
    
    path('admin', admin.site.urls),
    
    path("events/", include("django_eventstream.urls")),  # trailing slash required by django-eventstream mount
    
    path('api/auth/google', google_auth_start, name='google-auth-start'),
    path('api/auth/google/callback', google_auth_callback, name='google-auth-callback'),
    
    path('api/profile-img', UploadUserProfileImageView.as_view(), name='upload-profile-image'),
    path('api/auth', include('core.urls')),
    path('api/internships', include('internships.urls')),
    path('api/mentorships', include('mentorships.urls')),
    path('api/events/', include('events.urls')),  # deliberate trailing slash: keeps POST /api/events/ (collection) distinct from /api/events/<sqid>; APPEND_SLASH=False — no normalization
    path('api/payments', include('payments.urls')),
    path('api/feed', include('feed.urls')),
    path('api/posts', include('posts.urls')),
    path('api/notifications', include('notifications.urls')),
    path('api/reviews', include('reviews.urls')),

    path('api/students/resumes', ListStudentResumesView.as_view(), name='list-student-resumes'),
    path('api/students/resumes/upload', UploadStudentResumeView.as_view(), name='upload-student-resume'),
    path('api/students/resumes/<slug:sqid>', DeleteStudentResumeView.as_view(), name='delete-student-resume'),
]
