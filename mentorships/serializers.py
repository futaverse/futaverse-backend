from django.shortcuts import get_object_or_404

from rest_framework import serializers

from core.serializers import StudentInfoSerializer, AlumniInfoSerializer
from core.models import StudentProfile

from .models import Mentorship, MentorshipOffer, MentorshipApplication, MentorshipEngagement, MentorshipStatus

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
    student = serializers.SlugRelatedField(queryset=StudentProfile.objects.all(), slug_field='sqid', write_only=True)
    
    mentorship_info = MentorshipSerializer(source='mentorship', read_only=True)
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
    mentorship = serializers.SlugRelatedField(queryset=Mentorship.objects.all(), slug_field='sqid', write_only=True)
    
    mentorship_info = MentorshipSerializer(source='mentorship', read_only=True)
    student_info = StudentInfoSerializer(read_only=True, source='student')
    alumnus_info  = AlumniInfoSerializer(read_only=True, source='mentorship.alumnus')
    class Meta:
        model = MentorshipApplication
        exclude = ['deleted_at', 'is_deleted', 'id', 'student']
        read_only_fields = ['sqid', 'created_at', 'status', 'responded_at', 'student_info', 'alumnus_info']
        
class MentorshipEngagementSerializer(serializers.ModelSerializer):
    mentorship_info = MentorshipSerializer(source='mentorship', read_only=True)
    student_info = StudentInfoSerializer(read_only=True, source='student')
    alumnus_info = AlumniInfoSerializer(read_only=True, source='alumnus')
    class Meta:
        model = MentorshipEngagement
        exclude = ['deleted_at', 'is_deleted', 'id', 'mentorship', 'student', 'alumnus']
        read_only_fields = ['sqid', 'created_at']
        
class ManageMentorshipOfferSerializer(serializers.Serializer):
    offer_id = serializers.CharField()

    def validate(self, attrs):
        request = self.context["request"]
        offer_id = attrs["offer_id"]

        if not offer_id:
            raise serializers.ValidationError("Offer id is required.")

        offer = get_object_or_404(MentorshipOffer.objects.select_related("mentorship", "student", "mentorship__alumnus"),
            sqid=offer_id)

        if offer.student != request.user.student_profile:
            raise serializers.ValidationError("You are not authorized perform this action.")

        if offer.status != MentorshipStatus.PENDING:
            raise serializers.ValidationError(f"Offer has already been {offer.status.lower()}.")

        if not offer.mentorship.is_active:
            raise serializers.ValidationError("mentorship is not active.")

        if MentorshipEngagement.objects.filter(mentorship=offer.mentorship, student=offer.student).exists():
            raise serializers.ValidationError("You are already engaged in this mentorship.")

        attrs["offer"] = offer
        return attrs
        
class ManagementorshipApplicationSerializer(serializers.Serializer):
    application_id = serializers.CharField()

    def validate(self, attrs):
        request = self.context["request"]
        application_id = attrs["application_id"]

        if not application_id:
            raise serializers.ValidationError("Application ID is required.")

        application = get_object_or_404(MentorshipApplication.objects.select_related("mentorship", "student", "mentorship__alumnus"),
            sqid=application_id)

        if application.student != request.user.student_profile:
            raise serializers.ValidationError("You are not authorized to accept this mentorship application.")

        if application.status != MentorshipStatus.PENDING:
            raise serializers.ValidationError(f"Application has already been {application.status.lower()}.")

        if not application.mentorship.is_active:
            raise serializers.ValidationError("mentorship is not active.")

        if MentorshipEngagement.objects.filter(mentorship=application.mentorship, student=application.student).exists():
            raise serializers.ValidationError("You are already engaged in this mentorship.")

        attrs["application"] = application
        return attrs