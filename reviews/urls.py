from django.urls import path

from reviews.views import CreateReviewView, ListUserReviewsView, ListMyReviewsView

urlpatterns = [
    path("", CreateReviewView.as_view(), name="create-review"),
    path("/me", ListMyReviewsView.as_view(), name="list-my-reviews"),
    path("/<slug:sqid>", ListUserReviewsView.as_view(), name="list-reviews"),
    # path("/<slug:sqid>", RetrieveUpdateReviewView.as_view(), name="retrieve-update-review"),
]
