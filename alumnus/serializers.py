from rest_framework import serializers

from .models import AlumniProfile
from core.models import User, UserProfileImage

class AlumniProfileSerializer(serializers.ModelSerializer):
    previous_comps = serializers.ListField(child=serializers.CharField(), required=False)
    profile_img = serializers.SlugRelatedField(queryset=UserProfileImage.objects.all(), required=False, slug_field='sqid')
    
    class Meta:
        model = AlumniProfile
        exclude = ['user']
        

class AlumniInfoSerializer(serializers.ModelSerializer):
    # profile_img = serializers.SerializerMethodField()
    
    class Meta:
        model = AlumniProfile
        fields = ['sqid', 'firstname', 'lastname', 'middlename', 'gender', 'phone_num']
        read_only_fields = ['sqid']
        
    # def get_profile_img(self, obj):
    #     if obj.user.profile_img:
    #         return obj.user.profile_img.sqid
    #     return None 
    
class CreateAlumnusSerializer(serializers.ModelSerializer):
    profile = AlumniProfileSerializer(required=True, source='alumni_profile')
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    
    class Meta:
        model = User
        # fields = '__all__'
        exclude = ['is_active', 'is_staff', 'role', 'last_login']
        read_only_fields = ['sqid', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        profile_data = validated_data.pop('alumni_profile')
        profile_img = profile_data.pop('profile_img', None)
        
        validated_data['role'] = User.Role.ALUMNI
        user = super().create(validated_data)
        AlumniProfile.objects.create(user=user, **profile_data)
        
        if profile_img:
            profile_img.user = user
            profile_img.save()
        
        return user
    
