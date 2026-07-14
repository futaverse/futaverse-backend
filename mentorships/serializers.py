from django.shortcuts import get_object_or_404

from rest_framework import serializers

from core.serializers import StudentInfoSerializer, AlumniInfoSerializer
from core.models import StudentProfile

from .models import Mentorship, MentorshipOffer, MentorshipApplication, MentorshipEngagement, FocusArea, MentorshipCategory
from engagements.models import EngagementLifecycleStatus

from futaverse.serializers import StrictFieldsMixin

from engagements.serializers import (
    make_student_manage_offer_serializer,
    make_alumnus_manage_offer_serializer,
    make_student_manage_application_serializer,
    make_alumnus_manage_application_serializer,
)


class MentorshipSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    focus_areas = serializers.ListField(child=serializers.ChoiceField(choices=FocusArea.choices), required=False)
    category = serializers.ChoiceField(choices=MentorshipCategory.choices)

    class Meta:
        model = Mentorship
        exclude = ['is_active', 'deleted_at', 'is_deleted', 'id']
        read_only_fields = ['sqid', 'created_at', 'updated_at', 'alumnus', 'remaining_slots']

    def create(self, validated_data):
        available_slots = validated_data.get('available_slots', None)
        validated_data['remaining_slots'] = available_slots
        return super().create(validated_data)


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
    alumnus_info = AlumniInfoSerializer(read_only=True, source='mentorship.alumnus')

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        mentorship = validated_data['mentorship']
        student = validated_data['student']

        request = self.context["request"]
        if mentorship.alumnus != request.user.alumni_profile:
            raise serializers.ValidationError("You can only send offers for your own mentorships.")

        if not mentorship.is_active:
            raise serializers.ValidationError("This mentorship is inactive. You cannot send new offers.")

        if MentorshipOffer.objects.filter(mentorship=mentorship, student=student, status=EngagementLifecycleStatus.PENDING).exists():
            raise serializers.ValidationError({"detail": "You have already offered this mentorship to this student."})

        if MentorshipEngagement.objects.filter(mentorship=mentorship, student=student, status=MentorshipEngagement.EngagementStatus.ACTIVE).exists():
            raise serializers.ValidationError({"detail": "You are already engaged in this mentorship."})

        return validated_data

    class Meta:
        model = MentorshipOffer
        exclude = ['deleted_at', 'is_deleted', 'id']
        read_only_fields = ['sqid', 'created_at', 'status', 'responded_at']


class MentorshipApplicationSerializer(serializers.ModelSerializer):
    mentorship = serializers.SlugRelatedField(queryset=Mentorship.objects.all(), slug_field='sqid', write_only=True)

    mentorship_info = MentorshipSerializer(source='mentorship', read_only=True)
    student_info = StudentInfoSerializer(read_only=True, source='student')
    alumnus_info = AlumniInfoSerializer(read_only=True, source='mentorship.alumnus')

    class Meta:
        model = MentorshipApplication
        exclude = ['deleted_at', 'is_deleted', 'id', 'student']
        read_only_fields = ['sqid', 'created_at', 'status', 'responded_at', 'student_info', 'alumnus_info']

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        mentorship = validated_data['mentorship']
        student = self.context['request'].user.student_profile

        if not mentorship.is_active:
            raise serializers.ValidationError({"detail": "This mentorship is not active."})

        if MentorshipApplication.objects.filter(mentorship=mentorship, student=student).exists():
            raise serializers.ValidationError({"detail": "You have already applied for this mentorship."})

        return validated_data


class MentorshipEngagementSerializer(serializers.ModelSerializer):
    mentorship_info = MentorshipSerializer(source='mentorship', read_only=True)
    student_info = StudentInfoSerializer(read_only=True, source='student')
    alumnus_info = AlumniInfoSerializer(read_only=True, source='alumnus')

    class Meta:
        model = MentorshipEngagement
        exclude = ['deleted_at', 'is_deleted', 'id', 'mentorship', 'student', 'alumnus']
        read_only_fields = ['sqid', 'created_at']


StudentManageMentorshipOfferSerializer = make_student_manage_offer_serializer(
    MentorshipOffer, MentorshipEngagement, "mentorship"
)

AlumnusManageMentorshipOfferSerializer = make_alumnus_manage_offer_serializer(
    MentorshipOffer, "mentorship"
)

StudentManageMentorshipApplicationSerializer = make_student_manage_application_serializer(
    MentorshipApplication, MentorshipEngagement, "mentorship"
)

AlumnusManageMentorshipApplicationSerializer = make_alumnus_manage_application_serializer(
    MentorshipApplication, MentorshipEngagement, "mentorship"
)


class MentorshipEngagementFeedSerializer(serializers.ModelSerializer):
    mentorship_title = serializers.CharField(source='mentorship.title')
    mentor_name = serializers.CharField(source='alumnus.full_name')

    class Meta:
        model = MentorshipEngagement
        fields = ['sqid', 'mentorship_title', 'mentor_name', 'status']
