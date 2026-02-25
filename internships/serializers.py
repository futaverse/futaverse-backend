from rest_framework import serializers

from alumnus.serializers import AlumniInfoSerializer

from .models import Internship, InternshipApplication, InternshipOffer, InternshipEngagement, ApplicationResume
from students.models import StudentProfile
from students.serializers import StudentProfileSerializer, StudentInfoSerializer
from alumnus.models import AlumniProfile

from futaverse.serializers import StrictFieldsMixin

class InternshipSerializer(serializers.ModelSerializer):
    skills_required = serializers.ListField(child=serializers.CharField(), required=False)
    
    class Meta:
        model = Internship
        exclude = ['is_active', 'deleted_at', 'is_deleted']
        read_only_fields = ['sqid', 'created_at', 'updated_at', 'alumnus', 'is_active']
        
class InternshipStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Internship
        fields = ['sqid', 'is_active']
        read_only_fields = ['sqid']
        
class InternshipOfferSerializer(serializers.ModelSerializer):
    internship_id = serializers.SlugRelatedField(queryset=Internship.objects.all(), source='internship', write_only=True, slug_field='sqid')
    internship = InternshipSerializer( read_only=True)
    
    student_id = serializers.SlugRelatedField(queryset=StudentProfile.objects.all(), source='student', write_only=True, slug_field='sqid')
    student = StudentInfoSerializer(read_only=True)
    
    alumnus_info = AlumniInfoSerializer(read_only=True, source='internship.alumnus')
    
    class Meta:
        model = InternshipOffer
        fields = ['internship', 'student', 'internship_id', 'student_id', 'alumnus_info']
        read_only_fields = ['sqid', 'created_at', 'updated_at']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        internship = validated_data['internship']
        student = validated_data['student']
        
        if not internship.is_active:
            raise serializers.ValidationError("This internship is inactive. You cannot send new offers.")
        
        if InternshipOffer.objects.filter(internship=internship, student=student).exists():
            raise serializers.ValidationError({"detail": "You have already offered this internship."})
        
        return  validated_data
    
class InternshipApplicationSerializer(serializers.ModelSerializer):
    internship_id = serializers.SlugRelatedField(queryset=Internship.objects.all(), source='internship', write_only=True, slug_field='sqid')
    internship = InternshipSerializer(read_only=True)
    
    student = StudentInfoSerializer(read_only=True)
    
    resume = serializers.SlugRelatedField(queryset=ApplicationResume.objects.all(), required=False, write_only=True, slug_field='sqid')
    
    class Meta:
        model = InternshipApplication
        fields = ['internship', 'sqid', 'cover_letter', 'resume', 'student', 'internship_id']
        read_only_fields = ['sqid', 'created_at', 'updated_at', 'student', 'status', 'created_at', 'updated_at', 'deleted_at', 'is_deleted']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        internship = validated_data['internship']
        resume = validated_data.get('resume')
        
        student = self.context['request'].user.student_profile
        require_resume = internship.require_resume
        
        if internship.is_active is False:
            raise serializers.ValidationError({"detail": "This internship is no longer active."})
        
        if InternshipApplication.objects.filter(internship=internship, student=student).exists():
            raise serializers.ValidationError({"detail": "You have already applied for this internship."})
        
        if require_resume and not resume:
            raise serializers.ValidationError({"detail": "You must upload a resume before applying for this internship."})
        
        return validated_data
        
class ApplicationResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationResume
        fields = ['resume', 'sqid']
        read_only_fields = ['sqid', 'uploaded_at', 'application', 'student']
        
class InternshipEngagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternshipEngagement
        exclude = ['deleted_at', 'is_deleted']
        read_only_fields = ['sqid', 'created_at', 'updated_at']
        
        
   


        