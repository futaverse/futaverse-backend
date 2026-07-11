from django.test import TestCase

from engagements.views import (
    AcceptApplicationView, RejectApplicationView, WithdrawApplicationView,
    AcceptOfferView, RejectOfferView, WithdrawOfferView,
)
from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent


class GenericViewClassTests(TestCase):
    def test_accept_application_view_has_correct_permissions(self):
        self.assertEqual(AcceptApplicationView.permission_classes, [IsAuthenticatedAlumnus])

    def test_reject_application_view_has_correct_permissions(self):
        self.assertEqual(RejectApplicationView.permission_classes, [IsAuthenticatedAlumnus])

    def test_withdraw_application_view_has_correct_permissions(self):
        self.assertEqual(WithdrawApplicationView.permission_classes, [IsAuthenticatedStudent])

    def test_accept_offer_view_has_correct_permissions(self):
        self.assertEqual(AcceptOfferView.permission_classes, [IsAuthenticatedStudent])

    def test_reject_offer_view_has_correct_permissions(self):
        self.assertEqual(RejectOfferView.permission_classes, [IsAuthenticatedStudent])

    def test_withdraw_offer_view_has_correct_permissions(self):
        self.assertEqual(WithdrawOfferView.permission_classes, [IsAuthenticatedAlumnus])

    def test_accept_application_view_has_required_attributes(self):
        view = AcceptApplicationView()
        self.assertIsNone(view.application_model)
        self.assertIsNone(view.engagement_model)
        self.assertIsNone(view.engagement_serializer_class)
        self.assertIsNone(view.validation_serializer_class)
        self.assertIsNone(view.relation_name)

    def test_accept_application_view_can_be_subclassed(self):
        class Subclass(AcceptApplicationView):
            application_model = "Fake"
            engagement_model = "Fake"
            engagement_serializer_class = "Fake"
            validation_serializer_class = "Fake"
            relation_name = "test"

        self.assertEqual(Subclass.application_model, "Fake")
        self.assertEqual(Subclass.relation_name, "test")
        self.assertEqual(Subclass.permission_classes, [IsAuthenticatedAlumnus])

    def test_accept_offer_view_can_be_subclassed(self):
        class Subclass(AcceptOfferView):
            offer_model = "Fake"
            engagement_model = "Fake"
            engagement_serializer_class = "Fake"
            validation_serializer_class = "Fake"
            relation_name = "test"

        self.assertEqual(Subclass.relation_name, "test")
        self.assertEqual(Subclass.permission_classes, [IsAuthenticatedStudent])

    def test_all_views_are_api_view_subclasses(self):
        from rest_framework.views import APIView
        classes = [
            AcceptApplicationView, RejectApplicationView, WithdrawApplicationView,
            AcceptOfferView, RejectOfferView, WithdrawOfferView,
        ]
        for cls in classes:
            self.assertTrue(issubclass(cls, APIView), f"{cls.__name__} should be an APIView subclass")
