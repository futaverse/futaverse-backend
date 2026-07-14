from django.urls import path

from reviews.views import CreateReviewView, ListUserReviewsView, ListMyReviewsView, UpdateReview, RetrieveReviewView

urlpatterns = [
    path("", CreateReviewView.as_view(), name="create-review"),
    path("/me", ListMyReviewsView.as_view(), name="list-my-reviews"),
    path("/retrieve/<slug:sqid>", RetrieveReviewView.as_view(), name="retrieve-review"),
    path("/update/<slug:sqid>", UpdateReview.as_view(), name="update-review"),
    path("/<slug:sqid>", ListUserReviewsView.as_view(), name="list-reviews"),
]
