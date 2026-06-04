from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from futaverse.permissions import IsAuthenticatedStudent, IsAuthenticatedAlumnus

from drf_spectacular.utils import extend_schema

from .models import Review
from .serializers import ReviewSerializer, CreateReviewSerializer, UpdateReviewSerializer
from .schema import CREATEREVIEWSCHEMA
from .services import create_review

from core.models import User, StudentProfile, AlumniProfile

@extend_schema(tags=["Reviews"], summary="Create a review for an engagement.", **CREATEREVIEWSCHEMA)
class CreateReviewView(generics.CreateAPIView):
    serializer_class = CreateReviewSerializer
    permission_classes = [IsAuthenticatedStudent | IsAuthenticatedAlumnus]
    
    def perform_create(self, serializer):
        self.review = create_review(**serializer.validated_data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(ReviewSerializer(self.review).data, status=status.HTTP_201_CREATED)
    
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
            
        return Review.objects.filter(reviewee=profile.user).select_related("reviewee", "reviewer").order_by("-created_at")

@extend_schema(tags=["Reviews"], summary="List reviews for the logged in user")
class ListMyReviewsView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    
    def get_queryset(self):
        user = self.request.user
            
        return Review.objects.filter(reviewee=user).select_related("reviewee", "reviewer").order_by("-created_at")

class UpdateReview(generics.UpdateAPIView):
    serializer_class = UpdateReviewSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    lookup_field = "sqid"
    http_method_names = ["patch"]

    def get_queryset(self):
        return Review.objects.all()

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)  
        
        instance = self.get_object()
        return Response(ReviewSerializer(instance).data, status=status.HTTP_200_OK)
        
@extend_schema(tags=["Reviews"])
class RetrieveReviewView(generics.RetrieveAPIView):
    serializer_class = ReviewSerializer
    lookup_field = "sqid"
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    queryset = Review.objects.all().select_related("reviewee", "reviewer")