from django.shortcuts import get_object_or_404

from rest_framework import generics, status

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent
from futaverse.lib import MODELS

from .serializers import ShareEngagementSerializer, PostSerializer
from .services import share_engagement

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