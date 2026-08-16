from rest_framework import serializers

from core.models import LevelChoices, StudentProfile, StudentResume
from core.serializers import (
    AlumniInfoSerializer,
    StudentInfoSerializer,
    StudentResumeSerializer,
)
from engagements.models import Engagement, EngagementLifecycleStatus
from engagements.serializers import (
    make_alumnus_manage_application_serializer,
    make_alumnus_manage_offer_serializer,
    make_student_manage_application_serializer,
    make_student_manage_offer_serializer,
)
from engagements.services import get_engagement_detail

from .models import (
    Internship,
    InternshipApplication,
    InternshipEngagement,
    InternshipOffer,
)


class InternshipSerializer(serializers.ModelSerializer):
    skills_required = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    levels = serializers.ListField(
        child=serializers.ChoiceField(choices=LevelChoices.choices)
    )
    alumnus = serializers.CharField(source="alumnus.sqid", read_only=True)

    class Meta:
        model = Internship
        exclude = ["is_active", "deleted_at", "is_deleted", "id"]
        read_only_fields = ["sqid", "created_at", "updated_at", "alumnus", "is_active"]

    def create(self, validated_data):
        available_slots = validated_data.get("available_slots", None)
        validated_data["remaining_slots"] = available_slots
        return super().create(validated_data)

    def validate(self, attrs):
        validated_data = super().validate(attrs)

        end_date = validated_data.get("end_date")
        start_date = validated_data.get("start_date")
        if end_date and start_date and end_date <= start_date:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date."}
            )

        levels = validated_data.get("levels")
        if levels is not None and not levels:
            raise serializers.ValidationError(
                {"levels": "At least one level is required."}
            )

        stipend = validated_data.get("stipend")
        if stipend is not None and stipend < 0:
            raise serializers.ValidationError(
                {"stipend": "Stipend cannot be negative."}
            )

        return validated_data


class InternshipStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Internship
        fields = ["sqid", "is_active"]
        read_only_fields = ["sqid"]


class InternshipOfferSerializer(serializers.ModelSerializer):
    internship = serializers.SlugRelatedField(
        queryset=Internship.objects.all(), write_only=True, slug_field="sqid"
    )
    student = serializers.SlugRelatedField(
        queryset=StudentProfile.objects.all(), write_only=True, slug_field="sqid"
    )

    internship_info = InternshipSerializer(read_only=True, source="internship")
    student_info = StudentInfoSerializer(read_only=True, source="student")
    alumnus_info = AlumniInfoSerializer(read_only=True, source="internship.alumnus")

    class Meta:
        model = InternshipOffer
        fields = [
            "internship",
            "student",
            "internship_info",
            "student_info",
            "alumnus_info",
            "sqid",
        ]
        read_only_fields = ["sqid", "created_at", "updated_at"]

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        internship = validated_data["internship"]
        student = validated_data["student"]

        request = self.context["request"]
        if internship.alumnus != request.user.alumni_profile:
            raise serializers.ValidationError(
                "You can only send offers for your own internships."
            )

        if not internship.is_active:
            raise serializers.ValidationError(
                "This internship is inactive. You cannot send new offers."
            )

        if InternshipOffer.objects.filter(
            internship=internship, student=student
        ).exists():
            raise serializers.ValidationError(
                {"detail": "You have already offered this internship."}
            )

        if Engagement.objects.filter(
            engagement_type=Engagement.EngagementType.INTERNSHIP,
            student=student,
            status=Engagement.EngagementStatus.ACTIVE,
            internship_detail__internship=internship,
        ).exists():
            raise serializers.ValidationError(
                {"detail": "This student is already engaged in this internship."}
            )

        return validated_data


class InternshipApplicationSerializer(serializers.ModelSerializer):
    internship = serializers.SlugRelatedField(
        queryset=Internship.objects.all(), write_only=True, slug_field="sqid"
    )

    internship_info = InternshipSerializer(read_only=True, source="internship")
    student_info = StudentInfoSerializer(read_only=True, source="student")
    alumnus_info = AlumniInfoSerializer(read_only=True, source="internship.alumnus")

    resume = serializers.SlugRelatedField(
        queryset=StudentResume.objects.all(),
        required=False,
        write_only=True,
        slug_field="sqid",
    )
    resume_info = StudentResumeSerializer(read_only=True, source="resume")

    class Meta:
        model = InternshipApplication
        fields = [
            "sqid",
            "cover_letter",
            "resume",
            "resume_info",
            "internship",
            "internship_info",
            "student_info",
            "alumnus_info",
            "status",
            "created_at",
        ]
        read_only_fields = ["sqid", "created_at", "status"]

    def validate(self, attrs):
        validated_data = super().validate(attrs)

        internship = validated_data["internship"]
        resume = validated_data.get("resume")

        student = self.context["request"].user.student_profile
        require_resume = internship.require_resume

        if internship.is_active is False:
            raise serializers.ValidationError(
                {"detail": "This internship is no longer active."}
            )

        if InternshipApplication.objects.filter(
            internship=internship,
            student=student,
            status__in=[
                EngagementLifecycleStatus.ACCEPTED,
                EngagementLifecycleStatus.PENDING,
            ],
        ).exists():
            raise serializers.ValidationError(
                {"detail": "You have already applied for this internship."}
            )

        if require_resume and not resume:
            raise serializers.ValidationError(
                {
                    "detail": "You must upload a resume before applying for this internship."
                }
            )

        if resume and resume.student != student:
            raise serializers.ValidationError(
                {"detail": "This resume does not belong to you."}
            )

        return validated_data


class InternshipEngagementSerializer(serializers.ModelSerializer):
    internship_info = InternshipSerializer(
        read_only=True, source="internship_detail.internship"
    )
    student_info = StudentInfoSerializer(read_only=True, source="student")
    alumnus_info = AlumniInfoSerializer(read_only=True, source="alumnus")
    source = serializers.SerializerMethodField()
    source_id = serializers.SerializerMethodField()

    class Meta:
        model = Engagement
        fields = [
            "sqid",
            "status",
            "source",
            "source_id",
            "internship_info",
            "student_info",
            "alumnus_info",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_source(self, obj):
        detail = get_engagement_detail(obj)
        if detail is None:
            return None
        if detail.application_id is not None:
            return InternshipEngagement.Source.APPLICATION
        if detail.offer_id is not None:
            return InternshipEngagement.Source.OFFER
        return None

    def get_source_id(self, obj):
        detail = get_engagement_detail(obj)
        if detail is None:
            return None
        return detail.application_id or detail.offer_id


StudentManageInternshipOfferSerializer = make_student_manage_offer_serializer(
    InternshipOffer, "internship", Engagement.EngagementType.INTERNSHIP
)

AlumnusManageInternshipOfferSerializer = make_alumnus_manage_offer_serializer(
    InternshipOffer, "internship", Engagement.EngagementType.INTERNSHIP
)

StudentManageInternshipApplicationSerializer = (
    make_student_manage_application_serializer(
        InternshipApplication, "internship", Engagement.EngagementType.INTERNSHIP
    )
)

AlumnusManageInternshipApplicationSerializer = (
    make_alumnus_manage_application_serializer(
        InternshipApplication, "internship", Engagement.EngagementType.INTERNSHIP
    )
)


class InternshipEngagementFeedSerializer(serializers.ModelSerializer):
    internship_title = serializers.CharField(
        source="internship_detail.internship.title"
    )
    company = serializers.CharField(source="internship_detail.internship.company")
    alumnus_name = serializers.CharField(source="alumnus.full_name")

    class Meta:
        model = Engagement
        fields = ["sqid", "internship_title", "company", "alumnus_name", "status"]
