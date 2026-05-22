
from rest_framework import generics

from drf_spectacular.utils import extend_schema, extend_schema_view

from mentorships.models import Mentorship, MentorshipEngagement
from mentorships.serializers import MentorshipSerializer, MentorshipStatusSerializer, MentorshipEngagementSerializer
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

from feed.tasks import create_feed_event_task
from feed.models import FeedEvent

@extend_schema_view(
    list=extend_schema(summary="List mentorships (alumnus)"),
    create=extend_schema(summary="Create an mentorship (alumnus)"),
)
@extend_schema(tags=['Mentorships'])
class ListCreateMentorshipView(generics.ListCreateAPIView):
    serializer_class = MentorshipSerializer
    permission_classes = [IsAuthenticatedAlumnus]
    
    def get_queryset(self):
        user = self.request.user
        return Mentorship.objects.filter(alumnus=user.alumni_profile).select_related('alumnus')
    
    def perform_create(self, serializer):
        alumnus = self.request.user.alumni_profile
        mentorship = serializer.save(alumnus=alumnus)
        
        create_feed_event_task.delay(
            event_type=FeedEvent.EventType.MENTORSHIP_CREATED,
            related_object_id=mentorship.id,
            related_model='mentorship', 
            audience=FeedEvent.Audience.STUDENT, 
            data={
                'title': mentorship.title,
                'alumni': mentorship.alumnus.full_name,  
                'category': mentorship.category,
                'available_slots': mentorship.available_slots,
                'remaining_slots': mentorship.remaining_slots,
                'created_at': mentorship.created_at.isoformat(),
            }
        )

@extend_schema_view(
    retrieve=extend_schema(summary="Get an mentorship by id (alumnus)"),
    update=extend_schema(summary="Update an mentorship by id (alumnus)"),
    destroy=extend_schema(summary="Delete an mentorship by id (alumnus)"),
)
@extend_schema(tags=['Mentorships'], summary='Retrieve (GET), update (PATCH) and delete (DELETE) a mentorship by id (alumnus)')
class RetrieveUpdateDestroyMentorshipView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MentorshipSerializer
    permission_classes = [IsAuthenticatedAlumnus]
    http_method_names = ['get', 'patch', 'delete']
    lookup_field = 'sqid'
    
    def get_queryset(self):
        user = self.request.user
        return Mentorship.objects.filter(alumnus=user.alumni_profile).select_related('alumnus')
    
    def perform_destroy(self, instance):
        instance.soft_delete()
        
@extend_schema(tags=['Mentorships'], summary='Toggle active status of a mentorship (alumnus)')
class ToggleMentorshipActiveView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedAlumnus]
    queryset = Mentorship.objects.all()
    serializer_class = MentorshipStatusSerializer
    http_method_names = ['patch']
    lookup_field = 'sqid'
    
    def perform_update(self, serializer):
        mentorship = self.get_object()
        mentorship.toggle_active()
        
@extend_schema(tags=['Mentorship Engagements'], summary='List all mentorship engagements (alumnus and student)')
class ListMentorshipEngagementsView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipEngagementSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return MentorshipEngagement.objects.filter(alumnus=user.alumni_profile).select_related('mentorship', 'student', 'alumnus')
        
        elif user.role == User.Role.STUDENT:
            return MentorshipEngagement.objects.filter(student=user.student_profile).select_related('mentorship', 'student')
        
        return MentorshipEngagement.objects.none()
    
@extend_schema(tags=['Mentorship Engagements'], summary='Retrieve a mentorship engagement by id (alumnus and student)')
class RetrieveMentorshipEngagementView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipEngagementSerializer
    lookup_field = 'sqid'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return MentorshipEngagement.objects.filter(alumnus=user.alumni_profile).select_related('mentorship', 'student', 'alumnus')
        
        elif user.role == User.Role.STUDENT:
            return MentorshipEngagement.objects.filter(student=user.student_profile).select_related('mentorship', 'student')
        
        return MentorshipEngagement.objects.none()