from rest_framework import serializers

from alumnus.serializers import AlumniInfoSerializer
from students.serializers import StudentInfoSerializer

from .models import Mentorship, MentorshipOffer, MentorshipApplication, MentorshipRequest, MentorshipEngagement
from students.models import StudentProfile
from alumnus.models import AlumniProfile

from futaverse.serializers import StrictFieldsMixin

class MentorshipSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Mentorship
        exclude = ['is_active', 'deleted_at', 'is_deleted', 'id']
        read_only_fields = ['sqid', 'created_at', 'updated_at', 'alumnus', 'remaining_slots']
        
class MentorshipStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mentorship
        fields = ['sqid', 'is_active']
        read_only_fields = ['sqid']
        
class MentorshipOfferSerializer(serializers.ModelSerializer):
    mentorship = serializers.SlugRelatedField(queryset=Mentorship.objects.all(), slug_field='sqid', write_only=True)
    mentorship_info = MentorshipSerializer(source='mentorship', read_only=True)
    
    student = serializers.SlugRelatedField(queryset=StudentProfile.objects.all(), slug_field='sqid', write_only=True)
    student_info = StudentInfoSerializer(read_only=True, source='student')
    
    alumnus_info  = AlumniInfoSerializer(read_only=True, source='mentorship.alumnus')
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        mentorship = validated_data['mentorship']
        student = validated_data['student']
        
        if not mentorship.is_active:
            raise serializers.ValidationError("This mentorship is inactive. You cannot send new offers.")
        
        if MentorshipOffer.objects.filter(mentorship=mentorship, student=student).exists():
            raise serializers.ValidationError({"detail": "You have already offered this mentorship to this student."})
        
        return  validated_data
    
    class Meta:
        model = MentorshipOffer
        exclude = ['deleted_at', 'is_deleted', 'id']
        read_only_fields = ['sqid', 'created_at', 'status', 'responded_at']
        
class MentorshipApplicationSerializer(serializers.ModelSerializer):
    mentorship = serializers.SlugRelatedField(queryset=Mentorship.objects.all(), slug_field='sqid')
    alumnus_info  = AlumniInfoSerializer(read_only=True, source='mentorship.alumnus')
    
    class Meta:
        model = MentorshipApplication
        exclude = ['deleted_at', 'is_deleted', 'id', 'alumnus_info']
        read_only_fields = ['sqid', 'created_at', 'status', 'responded_at', 'student']
        
class MentorshipEngagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorshipEngagement
        exclude = ['deleted_at', 'is_deleted', 'id']
        read_only_fields = ['sqid', 'created_at']