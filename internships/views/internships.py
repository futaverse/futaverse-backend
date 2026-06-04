from django_q.tasks import async_task
from rest_framework import generics
from drf_spectacular.utils import extend_schema, extend_schema_view

from engagements.mixins import MarkEngagementCompletedMixin, MarkEngagementAcknowledgedMixin
from engagements.models import BaseEngagement

from internships.models import Internship, InternshipEngagement
from internships.serializers import InternshipSerializer, InternshipStatusSerializer, InternshipEngagementSerializer
from core.models import User
from feed.tasks import create_feed_event_task
from feed.models import FeedEvent

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

@extend_schema_view(
    list=extend_schema(summary="List internships (alumnus)"),
    create=extend_schema(summary="Create an internship (alumnus)"),
)
@extend_schema(tags=['Internships'])
class ListCreateInternshipView(generics.ListCreateAPIView):
    serializer_class = InternshipSerializer
    permission_classes = [IsAuthenticatedAlumnus]
    
    def get_queryset(self):
        user = self.request.user
        return Internship.objects.filter(alumnus=user.alumni_profile).select_related('alumnus').order_by('-created_at')
    
    def perform_create(self, serializer):
        alumnus = self.request.user.alumni_profile
        internship = serializer.save(alumnus=alumnus)
        
        async_task(create_feed_event_task, 
            event_type=FeedEvent.EventType.INTERNSHIP_CREATED,
            related_object_id=internship.id,
            related_model='internship',  
            audience=FeedEvent.Audience.STUDENT,
            data={
                'title':   internship.title,
                'alumni': internship.alumnus.full_name,  
                'work_mode': internship.work_mode,
                'engagement_type': internship.engagement_type,
                'stipend': str(internship.stipend),
                'is_paid': internship.is_paid,
                'available_slots': internship.available_slots,
                'remaining_slots': internship.remaining_slots,
                'created_at': internship.created_at.isoformat(),
            }
        )

@extend_schema_view(
    retrieve=extend_schema(summary="Get an internship by id (alumnus)"),
    update=extend_schema(summary="Update an internship by id (alumnus)"),
    destroy=extend_schema(summary="Delete an internship by id (alumnus)"),
)
@extend_schema(tags=['Internships']) 
class RetrieveUpdateDestroyInternshipView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InternshipSerializer
    http_method_names = ['patch', 'get', 'delete']
    permission_classes = [IsAuthenticatedAlumnus]
    lookup_field = 'sqid'
    
    def get_queryset(self):
        user = self.request.user
        return Internship.objects.filter(alumnus=user.alumni_profile).select_related('alumnus')
    
    def perform_destroy(self, instance):
        instance.soft_delete()
    
@extend_schema(tags=['Internships'], summary='Toggle internship active status (alumnus)')
class ToggleInternshipActiveView(generics.UpdateAPIView):
    queryset = Internship.objects.all()
    serializer_class = InternshipStatusSerializer
    http_method_names = ['patch']
    permission_classes = [IsAuthenticatedAlumnus]
    lookup_field = 'sqid'
    
    def perform_update(self, serializer):
        internship = self.get_object()
        internship.toggle_active()
    
@extend_schema(tags=['Internship Engagements'], summary='List all internship engagements (alumnus and student)')
class ListInternshipEngagementsView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = InternshipEngagementSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return InternshipEngagement.objects.filter(alumnus=user.alumni_profile).select_related('internship', 'student', 'alumnus')
        
        elif user.role == User.Role.STUDENT:
            return InternshipEngagement.objects.filter(student=user.student_profile).select_related('internship', 'student', 'alumnus')
        
        return InternshipEngagement.objects.none()
    
@extend_schema(tags=['Internship Engagements'], summary='Retrieve an internship engagement by id (alumnus and student)')
class RetrieveInternshipEngagementView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = InternshipEngagementSerializer
    lookup_field = 'sqid'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.ALUMNI:
            return InternshipEngagement.objects.filter(alumnus=user.alumni_profile).select_related('Internship', 'student', 'alumnus')
        
        elif user.role == User.Role.STUDENT:
            return InternshipEngagement.objects.filter(student=user.student_profile).select_related('Internship', 'student')
        
        return InternshipEngagement.objects.none()

@extend_schema(tags=['Internship Engagements'], summary='Mark an internship engagement as completed (alumnus)') 
class MarkInternshipCompletedView(MarkEngagementCompletedMixin, generics.UpdateAPIView):
    queryset = InternshipEngagement.objects.all()
    engagement_type = 'internship_engagement'
    serializer_class = InternshipEngagementSerializer

@extend_schema(tags=['Internship Engagements'], summary='Mark an internship engagement as acknowledged (student)')            
class MarkInternshipAcknowledgedView(MarkEngagementAcknowledgedMixin, generics.UpdateAPIView):
    queryset = InternshipEngagement.objects.all()
    engagement_type = 'internship_engagement'
    serializer_class = InternshipEngagementSerializer