from rest_framework import serializers

from .models import StudentProfile
from core.models import User, UserProfileImage

from .models import StudentResume

class StudentProfileSerializer(serializers.ModelSerializer):
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    profile_img = serializers.SlugRelatedField(queryset=UserProfileImage.objects.all(), required=False, slug_field='sqid')
    
    class Meta:
        model = StudentProfile
        exclude = ['user', 'id', 'is_deleted', 'deleted_at']
        
class StudentInfoSerializer(serializers.ModelSerializer):
    # profile_img = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentProfile
        fields = ['sqid', 'firstname', 'lastname', 'middlename', 'gender', 'phone_num', 'matric_no', 'department', 'faculty', 'level']        

class CreateStudentSerializer(serializers.ModelSerializer):
    profile = StudentProfileSerializer(required=True, source='student_profile')
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    
    class Meta:
        model = User
        exclude = ['is_active', 'is_staff', 'role', 'last_login', 'id']
        read_only_fields = ['sqid', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        profile_data = validated_data.pop('student_profile')
        profile_img = profile_data.pop('profile_img', None)
        
        validated_data['role'] = User.Role.STUDENT
        user = super().create(validated_data)
        StudentProfile.objects.create(user=user, **profile_data)
        
        if profile_img:
            profile_img.user = user
            profile_img.save()
        
        return user
    
class StudentResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentResume
        fields = ['resume']
        read_only_fields = ['sqid', 'student', 'uploaded_at']

    
