from django.urls import path

from reviews.views import (
    CreateReviewView,
    ListReviewsView,
    RetrieveUpdateReviewView
)

urlpatterns = [
    path("", CreateReviewView.as_view(), name="create-review"),
    path("/<slug:user_sqid>", ListReviewsView.as_view(), name="list-reviews"),
    path("/<slug:sqid>", RetrieveUpdateReviewView.as_view(), name="retrieve-update-review"),
]
