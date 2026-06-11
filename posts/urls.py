from django.urls import path

from .views import ShareEngagementView, ListMyPostsView, ListUserPostsView, ShareEngagementCompletionView

urlpatterns = [
    path('/share-engagement', ShareEngagementView.as_view(), name='share-engagement'),
    path('/share-engagement-completion', ShareEngagementCompletionView.as_view(), name='share-engagement-completion'),
    
    path('/me', ListMyPostsView.as_view(), name='list-my-posts'),
    path('/user/<str:user_id>', ListUserPostsView.as_view(), name='list-user-posts'),
]