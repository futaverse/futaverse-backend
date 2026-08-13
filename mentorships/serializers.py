from django.shortcuts import get_object_or_404

from rest_framework import serializers

from core.serializers import StudentInfoSerializer, AlumniInfoSerializer
from core.models import StudentProfile

from .models import Mentorship, MentorshipOffer, MentorshipApplication, MentorshipEngagement, FocusArea, MentorshipCategory
from engagements.models import Engagement, EngagementLifecycleStatus
from engagements.services import get_engagement_detail

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

        if Engagement.objects.filter(
            engagement_type=Engagement.EngagementType.MENTORSHIP,
            student=student,
            status=Engagement.EngagementStatus.ACTIVE,
            mentorship_detail__mentorship=mentorship,
        ).exists():
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
    mentorship_info = MentorshipSerializer(read_only=True, source='mentorship_detail.mentorship')
    student_info = StudentInfoSerializer(read_only=True, source='student')
    alumnus_info = AlumniInfoSerializer(read_only=True, source='alumnus')
    source = serializers.SerializerMethodField()
    source_id = serializers.SerializerMethodField()

    class Meta:
        model = Engagement
        fields = [
            'sqid', 'status', 'source', 'source_id',
            'mentorship_info', 'student_info', 'alumnus_info',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_source(self, obj):
        detail = get_engagement_detail(obj)
        if detail is None:
            return None
        if detail.application_id is not None:
            return MentorshipEngagement.Source.APPLICATION
        if detail.offer_id is not None:
            return MentorshipEngagement.Source.OFFER
        return None

    def get_source_id(self, obj):
        detail = get_engagement_detail(obj)
        if detail is None:
            return None
        return detail.application_id or detail.offer_id


StudentManageMentorshipOfferSerializer = make_student_manage_offer_serializer(
    MentorshipOffer, "mentorship", Engagement.EngagementType.MENTORSHIP
)

AlumnusManageMentorshipOfferSerializer = make_alumnus_manage_offer_serializer(
    MentorshipOffer, "mentorship", Engagement.EngagementType.MENTORSHIP
)

StudentManageMentorshipApplicationSerializer = make_student_manage_application_serializer(
    MentorshipApplication, "mentorship", Engagement.EngagementType.MENTORSHIP
)

AlumnusManageMentorshipApplicationSerializer = make_alumnus_manage_application_serializer(
    MentorshipApplication, "mentorship", Engagement.EngagementType.MENTORSHIP
)


class MentorshipEngagementFeedSerializer(serializers.ModelSerializer):
    mentorship_title = serializers.CharField(source='mentorship_detail.mentorship.title')
    mentor_name = serializers.CharField(source='alumnus.full_name')

    class Meta:
        model = Engagement
        fields = ['sqid', 'mentorship_title', 'mentor_name', 'status']
