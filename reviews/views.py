from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.exceptions import ValidationError

from futaverse.permissions import IsAuthenticatedStudent, IsAuthenticatedAlumnus

from drf_spectacular.utils import extend_schema

from .models import Review
from .serializers import ReviewSerializer, CreateReviewSerializer
from .schema import CREATEREVIEWSCHEMA
from .services import create_review

from core.models import User, StudentProfile, AlumniProfile

@extend_schema(tags=["Reviews"], summary="Create a review for an engagement.", **CREATEREVIEWSCHEMA)
class CreateReviewView(generics.CreateAPIView):
    serializer_class = CreateReviewSerializer
    permission_classes = [IsAuthenticatedStudent | IsAuthenticatedAlumnus]
    
    def perform_create(self, serializer):
        create_review(**serializer.validated_data)
    
@extend_schema(tags=["Reviews"], summary="List reviews for a user")
class ListUserReviewsView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    
    def get_queryset(self):
        sqid = self.kwargs.get("sqid")
        role = self.request.query_params.get("role")
        
        if not role or not role in [User.Role.ALUMNI, User.Role.STUDENT]:
            raise ValidationError({"details": "Role query parameter is required and must be either 'alumni' or 'student'."})
        
        if role == User.Role.STUDENT:
            profile = get_object_or_404(StudentProfile, sqid=sqid)
        elif role == User.Role.ALUMNI:
            profile = get_object_or_404(AlumniProfile, sqid=sqid)
            
        return Review.objects.filter(reviewee=profile.user).order_by("-created_at")
    
@extend_schema(tags=["Reviews"], summary="List reviews for the logged in user")
class ListMyReviewsView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    
    def get_queryset(self):
        user = self.request.user
            
        print("User:", user)
        return Review.objects.filter(reviewee=user).order_by("-created_at")
        # return Review.objects.all()

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
