from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from futaverse.permissions import IsAuthenticatedStudent, IsAuthenticatedAlumnus

from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Review
from .serializers import ReviewSerializer, CreateReviewSerializer
from .selectors import get_reviews_for_user
from .permissions import IsReviewer

@extend_schema(tags=["Reviews"], summary="Create a review for an engagement")
class CreateReviewView(generics.CreateAPIView):
    serializer_class = CreateReviewSerializer
    permission_classes = [IsAuthenticatedStudent | IsAuthenticatedAlumnus]
    
@extend_schema(tags=["Reviews"])
@extend_schema_view(
    get=extend_schema(summary="List reviews for a user"),
)
class ListReviewsView(generics.ListAPIView):
    """List all reviews for a specific user (as reviewee)."""
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        from core.models import User
        
        user_sqid = self.kwargs.get("user_sqid")
        try:
            user = User.objects.get(sqid=user_sqid)
            return get_reviews_for_user(user)
        except User.DoesNotExist:
            return Review.objects.none()


# @extend_schema(tags=["Reviews"])
# @extend_schema_view(
#     get=extend_schema(summary="Retrieve a review"),
#     patch=extend_schema(summary="Update a review"),
#     put=extend_schema(summary="Update a review"),
# )
# class RetrieveUpdateReviewView(generics.RetrieveUpdateAPIView):
#     """Retrieve or update a review."""
#     serializer_class = ReviewSerializer
#     lookup_field = "sqid"
#     permission_classes = [IsAuthenticated, IsReviewer]
    
#     def get_queryset(self):
#         return Review.objects.all()
    
#     def get_object(self):
#         from reviews.selectors import get_review
#         from django.contrib.auth.models import AnonymousUser
        
#         sqid = self.kwargs.get(self.lookup_field)
#         try:
#             review = Review.objects.get(sqid=sqid)
#             self.check_object_permissions(self.request, review)
#             return review
#         except Review.DoesNotExist:
#             self.kwargs[self.lookup_field] = None
#             self.check_object_permissions(self.request, None)
    
#     def get_serializer_class(self):
#         if self.request.method in ["PATCH", "PUT"]:
#             return UpdateReviewSerializer
#         return ReviewSerializer
    
#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop("partial", False)
#         review = self.get_object()
        
#         serializer = self.get_serializer(review, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         updated_review = serializer.save()
        
#         output_serializer = ReviewSerializer(updated_review)
#         return Response(output_serializer.data, status=status.HTTP_200_OK)
