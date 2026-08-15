from django.shortcuts import get_object_or_404
from rest_framework import serializers

from engagements.models import Engagement, EngagementLifecycleStatus


def make_student_manage_offer_serializer(offer_model, relation_name, engagement_type):
    detail_related = f"{engagement_type.removesuffix('_engagement')}_detail"

    class StudentManageOfferSerializer(serializers.Serializer):
        offer_id = serializers.CharField()

        def validate(self, attrs):
            request = self.context["request"]
            offer_id = attrs["offer_id"]

            if not offer_id:
                raise serializers.ValidationError("Offer id is required.")

            offer = get_object_or_404(
                offer_model.objects.select_related(
                    relation_name, "student", f"{relation_name}__alumnus"
                ),
                sqid=offer_id,
            )

            if offer.student != request.user.student_profile:
                raise serializers.ValidationError(
                    {"detail": "You are not authorized to perform this action."}
                )

            if offer.status != EngagementLifecycleStatus.PENDING:
                raise serializers.ValidationError(
                    {"detail": f"This offer has already been {offer.status.lower()}."}
                )

            parent = getattr(offer, relation_name)
            if not parent.is_active:
                raise serializers.ValidationError(
                    {"detail": "This opportunity is not active."}
                )

            if Engagement.objects.filter(
                engagement_type=engagement_type,
                student=offer.student,
                status=Engagement.EngagementStatus.ACTIVE,
                **{f"{detail_related}__{relation_name}": parent},
            ).exists():
                raise serializers.ValidationError(
                    {"detail": "You are already engaged in this opportunity."}
                )

            attrs["offer"] = offer
            return attrs

    return StudentManageOfferSerializer


def make_alumnus_manage_offer_serializer(offer_model, relation_name, engagement_type):
    detail_related = f"{engagement_type.removesuffix('_engagement')}_detail"

    class AlumnusManageOfferSerializer(serializers.Serializer):
        offer_id = serializers.CharField()

        def validate(self, attrs):
            request = self.context["request"]
            offer_id = attrs["offer_id"]

            if not offer_id:
                raise serializers.ValidationError("Offer id is required.")

            offer = get_object_or_404(
                offer_model.objects.select_related(
                    relation_name, "student", f"{relation_name}__alumnus"
                ),
                sqid=offer_id,
            )

            parent = getattr(offer, relation_name)
            if parent.alumnus != request.user.alumni_profile:
                raise serializers.ValidationError(
                    {"detail": "You are not authorized to withdraw this offer."}
                )

            if offer.status != EngagementLifecycleStatus.PENDING:
                raise serializers.ValidationError(
                    {"detail": f"This offer has already been {offer.status.lower()}."}
                )

            if not parent.is_active:
                raise serializers.ValidationError(
                    {"detail": "This opportunity is not active."}
                )

            attrs["offer"] = offer
            return attrs

    return AlumnusManageOfferSerializer


def make_student_manage_application_serializer(application_model, relation_name, engagement_type):
    detail_related = f"{engagement_type.removesuffix('_engagement')}_detail"

    class StudentManageApplicationSerializer(serializers.Serializer):
        application_id = serializers.CharField()

        def validate(self, attrs):
            request = self.context["request"]
            application_id = attrs["application_id"]

            if not application_id:
                raise serializers.ValidationError("Application ID is required.")

            application = get_object_or_404(
                application_model.objects.select_related(
                    relation_name, "student", f"{relation_name}__alumnus"
                ),
                sqid=application_id,
            )

            if application.student != request.user.student_profile:
                raise serializers.ValidationError(
                    {"detail": "You are not authorized to perform this action."}
                )

            if application.status != EngagementLifecycleStatus.PENDING:
                raise serializers.ValidationError(
                    {"detail": f"Application has already been {application.status.lower()}."}
                )

            parent = getattr(application, relation_name)
            if not parent.is_active:
                raise serializers.ValidationError(
                    {"detail": "This opportunity is not active."}
                )

            if Engagement.objects.filter(
                engagement_type=engagement_type,
                student=application.student,
                status=Engagement.EngagementStatus.ACTIVE,
                **{f"{detail_related}__{relation_name}": parent},
            ).exists():
                raise serializers.ValidationError(
                    {"detail": "You are already engaged in this opportunity."}
                )

            attrs["application"] = application
            return attrs

    return StudentManageApplicationSerializer


def make_alumnus_manage_application_serializer(application_model, relation_name, engagement_type):
    detail_related = f"{engagement_type.removesuffix('_engagement')}_detail"

    class AlumnusManageApplicationSerializer(serializers.Serializer):
        application_id = serializers.CharField()

        def validate(self, attrs):
            request = self.context["request"]
            application_id = attrs["application_id"]

            if not application_id:
                raise serializers.ValidationError("Application ID is required.")

            application = get_object_or_404(
                application_model.objects.select_related(
                    relation_name, "student", f"{relation_name}__alumnus"
                ),
                sqid=application_id,
            )

            parent = getattr(application, relation_name)
            if parent.alumnus != request.user.alumni_profile:
                raise serializers.ValidationError(
                    {"detail": "You are not authorized to manage this application."}
                )

            if application.status != EngagementLifecycleStatus.PENDING:
                raise serializers.ValidationError(
                    {"detail": f"Application has already been {application.status.lower()}."}
                )

            if not parent.is_active:
                raise serializers.ValidationError(
                    {"detail": "This opportunity is not active."}
                )

            if Engagement.objects.filter(
                engagement_type=engagement_type,
                student=application.student,
                status=Engagement.EngagementStatus.ACTIVE,
                **{f"{detail_related}__{relation_name}": parent},
            ).exists():
                raise serializers.ValidationError(
                    {"detail": "This student is already engaged in this opportunity."}
                )

            attrs["application"] = application
            return attrs

    return AlumnusManageApplicationSerializer
