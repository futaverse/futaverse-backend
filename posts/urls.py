from django.urls import path

from .views import ShareEngagementView

urlpatterns = [
    path('/share-engagement', ShareEngagementView.as_view(), name='share-engagement'),
]