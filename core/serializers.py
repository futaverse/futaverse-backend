from rest_framework import serializers
from .models import UserProfileImage, User, OTP

class UserProfileImageSerializer(serializers.ModelSerializer):
    url: str = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = UserProfileImage
        fields = ['sqid', 'image', 'url']
        
    def get_url(self, obj):
        return obj.image.url
        
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
            raise serializers.ValidationError({"email": "User with the provided email not found"})
        
        try:
            otp_instance = user.otp
        except OTP.DoesNotExist:
           raise serializers.ValidationError({"otp": "No OTP found"})

        self.user = user
        self.otp_instance = otp_instance
        self.otp = otp
        
        return validated_data
    
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