from django.contrib.auth import authenticate

from rest_framework import serializers, exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema_field

from .models import UserProfileImage, User, OTP, StudentProfile, StudentResume, AlumniProfile

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password
        )

        if not user:
            existing_user = User.objects.filter(email=email).first()

            if existing_user:
                raise exceptions.AuthenticationFailed(
                    detail="Incorrect password.",
                    code="incorrect_password"
                )

            raise exceptions.AuthenticationFailed(
                detail="No account found with this email.",
                code="user_not_found"
            )

        return super().validate(attrs)

class UserProfileImageSerializer(serializers.ModelSerializer):
    url: str = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = UserProfileImage
        fields = ['sqid', 'image', 'url']
        
    def get_url(self, obj):
        return obj.image.url
        
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        email = validated_data.get("email")
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email"})
        
        self.user = user
        self.email = email
        
        return validated_data
    
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, write_only=True, min_length=6, max_length=6)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        email = validated_data.get("email")
        otp = validated_data.get("otp")
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email"})
        
        try:
            otp_instance = user.otp
        except OTP.DoesNotExist:
           raise serializers.ValidationError({"otp": "No OTP found"})

        self.user = user
        self.otp_instance = otp_instance
        self.otp = otp
        
        return validated_data
    
class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    
class StudentProfileSerializer(serializers.ModelSerializer):
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    profile_img = serializers.SlugRelatedField(queryset=UserProfileImage.objects.all(), required=False, slug_field='sqid')
    
    class Meta:
        model = StudentProfile
        exclude = ['user', 'id', 'is_deleted', 'deleted_at']
        read_only_fields = ['avg_rating', 'total_reviews']
        
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
        fields = ['email', 'password', 'profile']
        read_only_fields = ['sqid', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        profile_data = validated_data.pop('student_profile')
        profile_img = profile_data.pop('profile_img', None)
        
        validated_data['role'] = User.Role.STUDENT
        user = User.objects.create_user(**validated_data)
        StudentProfile.objects.create(user=user, **profile_data)
        
        if profile_img:
            profile_img.user = user
            profile_img.save()
        
        return user
    
class StudentResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentResume
        fields = ['sqid', 'resume', 'filename', 'uploaded_at']
        read_only_fields = ['sqid', 'student', 'uploaded_at']
        
class AlumniProfileSerializer(serializers.ModelSerializer):
    previous_comps = serializers.ListField(child=serializers.CharField(), required=False)
    profile_img = serializers.SlugRelatedField(queryset=UserProfileImage.objects.all(), required=False, slug_field='sqid')
    
    class Meta:
        model = AlumniProfile
        exclude = ['user', 'id', 'is_deleted', 'deleted_at']
        read_only_fields = ['avg_rating', 'total_reviews']

class AlumniInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlumniProfile
        fields = ['sqid', 'firstname', 'lastname', 'middlename', 'gender', 'phone_num']
        read_only_fields = ['sqid']
        
class CreateAlumnusSerializer(serializers.ModelSerializer):
    profile = AlumniProfileSerializer(required=True, source='alumni_profile')
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'profile']
        read_only_fields = ['sqid', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        profile_data = validated_data.pop('alumni_profile')
        profile_img = profile_data.pop('profile_img', None)
        
        validated_data['role'] = User.Role.ALUMNI
        user = User.objects.create_user(**validated_data)
        AlumniProfile.objects.create(user=user, **profile_data)
        
        if profile_img:
            profile_img.user = user
            profile_img.save()
        
        return user

class StudentMeProfileSerializer(StudentProfileSerializer):
    profile_img_url = serializers.SerializerMethodField()
    resumes = StudentResumeSerializer(many=True, read_only=True)

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_profile_img_url(self, obj):
        image = obj.user.profile_img.order_by('-uploaded_at').first()
        return image.image.url if image else None

class AlumniMeProfileSerializer(AlumniProfileSerializer):
    profile_img_url = serializers.SerializerMethodField()

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_profile_img_url(self, obj):
        image = obj.user.profile_img.order_by('-uploaded_at').first()
        return image.image.url if image else None

class StudentMeResponseSerializer(serializers.ModelSerializer):
    profile = StudentMeProfileSerializer(read_only=True, source='student_profile')

    class Meta:
        model = User
        fields = ['sqid', 'email', 'role', 'created_at', 'profile']
        read_only_fields = fields

class AlumniMeResponseSerializer(serializers.ModelSerializer):
    profile = AlumniMeProfileSerializer(read_only=True, source='alumni_profile')

    class Meta:
        model = User
        fields = ['sqid', 'email', 'role', 'created_at', 'profile']
        read_only_fields = fields

class MeSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['sqid', 'email', 'role', 'created_at', 'profile']
        read_only_fields = fields

    def get_profile(self, user):
        if user.role == User.Role.STUDENT:
            return StudentMeProfileSerializer(user.student_profile).data
        if user.role == User.Role.ALUMNI:
            return AlumniMeProfileSerializer(user.alumni_profile).data
        return None

