from django.db import transaction

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent


class AcceptApplicationView(APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None

    application_model = None
    engagement_model = None
    engagement_serializer_class = None
    validation_serializer_class = None
    relation_name = None

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.validation_serializer_class(
            data={"application_id": kwargs.get("application_id")},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]

        parent = getattr(application, self.relation_name)
        student = application.student
        alumnus = parent.alumnus

        engagement = self.engagement_model.objects.create(
            **{self.relation_name: parent},
            student=student,
            alumnus=alumnus,
            source=self.engagement_model.Source.APPLICATION,
            source_id=application.id,
        )

        application.accept()
        parent.decrement_remaining_slots()

        return Response(
            {
                "detail": "Application accepted successfully.",
                "engagement": self.engagement_serializer_class(engagement).data,
            },
            status=status.HTTP_201_CREATED,
        )


class RejectApplicationView(APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None

    validation_serializer_class = None

    def post(self, request, *args, **kwargs):
        serializer = self.validation_serializer_class(
            data={"application_id": kwargs.get("application_id")},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]

        application.reject()

        return Response(
            {"detail": "Application rejected successfully."},
            status=status.HTTP_200_OK,
        )


class WithdrawApplicationView(APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None

    validation_serializer_class = None

    def post(self, request, *args, **kwargs):
        serializer = self.validation_serializer_class(
            data={"application_id": kwargs.get("application_id")},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]

        application.withdraw()

        return Response(
            {"detail": "Application withdrawn successfully."},
            status=status.HTTP_200_OK,
        )


class AcceptOfferView(APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None

    offer_model = None
    engagement_model = None
    engagement_serializer_class = None
    validation_serializer_class = None
    relation_name = None

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.validation_serializer_class(
            data={"offer_id": kwargs.get("offer_id")},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        offer = serializer.validated_data["offer"]

        parent = getattr(offer, self.relation_name)
        student = offer.student
        alumnus = parent.alumnus

        engagement = self.engagement_model.objects.create(
            **{self.relation_name: parent},
            student=student,
            alumnus=alumnus,
            source=self.engagement_model.Source.OFFER,
            source_id=offer.id,
        )

        offer.accept()
        parent.decrement_remaining_slots()

        return Response(
            {
                "detail": "Offer accepted successfully.",
                "engagement": self.engagement_serializer_class(engagement).data,
            },
            status=status.HTTP_201_CREATED,
        )


class RejectOfferView(APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None

    validation_serializer_class = None

    def post(self, request, *args, **kwargs):
        serializer = self.validation_serializer_class(
            data={"offer_id": kwargs.get("offer_id")},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        offer = serializer.validated_data["offer"]

        offer.reject()

        return Response(
            {"detail": "Offer rejected successfully."},
            status=status.HTTP_200_OK,
        )


class WithdrawOfferView(APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None

    validation_serializer_class = None

    def post(self, request, *args, **kwargs):
        serializer = self.validation_serializer_class(
            data={"offer_id": kwargs.get("offer_id")},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        offer = serializer.validated_data["offer"]

        offer.withdraw()

        return Response(
            {"detail": "Offer withdrawn successfully."},
            status=status.HTTP_200_OK,
        )
