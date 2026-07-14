from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from core.models import User
from futaverse.permissions import IsAuthenticatedStudent

from .serializers import ShareEngagementSerializer, PostSerializer, ShareEngagementCompletionSerializer
from .services import share_engagement, share_engagement_completion
from .models import Post

@extend_schema(tags=['Posts'], summary="Share an internship or mentorship engagement as a post (student)")
class ShareEngagementView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = ShareEngagementSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        content = validated_data.get('content')
        engagement = validated_data['engagement']

        post = share_engagement(
            user=request.user,
            engagement=engagement,
            custom_text=content
        )

        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)

@extend_schema(tags=['Posts'], summary="List all public posts shared by the logged in user")
class ListMyPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    queryset = Post.objects.none()
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        return Post.objects.filter(author=user, is_public=True).order_by('-created_at')

@extend_schema(tags=['Posts'], summary="List all public posts shared by a specific user")    
class ListUserPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.none()
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        
        user = get_object_or_404(User, sqid=user_id)
        
        return Post.objects.filter(author=user, is_public=True).order_by('-created_at')
    
@extend_schema(tags=['Posts'], summary="Share the completion of an internship or mentorship engagement as a post (student)")
class ShareEngagementCompletionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = ShareEngagementCompletionSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        content = validated_data.get('content')
        engagement = validated_data['engagement']

        post = share_engagement_completion(
            user=request.user,
            engagement=engagement,
            custom_text=content
        )

        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)
        
        