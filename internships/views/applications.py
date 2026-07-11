from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from drf_spectacular.utils import extend_schema

from internships.models import InternshipApplication, ApplicationResume, InternshipEngagement
from internships.serializers import (
    InternshipApplicationSerializer,
    ApplicationResumeSerializer,
    StudentManageInternshipApplicationSerializer,
    AlumnusManageInternshipApplicationSerializer,
    InternshipEngagementSerializer,
)
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent
from futaverse.utils.supabase import upload_file_to_supabase

from engagements.helpers import queryset_by_role
from engagements.views import AcceptApplicationView, RejectApplicationView, WithdrawApplicationView


@extend_schema(tags=['Internship Applications'], summary='Apply for an internship (student)')
class CreateInternshipApplicationView(generics.CreateAPIView):
    serializer_class = InternshipApplicationSerializer
    permission_classes = [IsAuthenticatedStudent]

    @transaction.atomic
    def perform_create(self, serializer):
        resume = serializer.validated_data.pop('resume', None)
        student = self.request.user.student_profile

        application = serializer.save(student=student)

        if resume:
            resume.application = application
            resume.save(update_fields=['application'])


@extend_schema(tags=['Internship Applications'], summary='List all internship applications (alumnus and student)')
class ListInternshipApplicationsView(generics.ListAPIView):
    serializer_class = InternshipApplicationSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            InternshipApplication,
            alumnus_filter={
                "internship__alumnus": self.request.user.alumni_profile,
                "status": "pending",
            },
            student_filter={
                "student": self.request.user.student_profile,
                "status": "pending",
            },
            select_related=("internship", "student", "resume"),
            order_by="-created_at",
        )


@extend_schema(tags=['Internship Applications'], summary='Retrieve an internship application by id (alumnus and student)')
class RetrieveInternshipApplicationView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = InternshipApplicationSerializer
    lookup_field = 'sqid'

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            InternshipApplication,
            alumnus_filter={"internship__alumnus": self.request.user.alumni_profile},
            student_filter={"student": self.request.user.student_profile},
            select_related=("internship", "student", "internship__alumnus"),
        )


@extend_schema(tags=['Internship Applications'], summary='Upload a resume for an internship application (student)')
class UploadApplicationResumeView(generics.CreateAPIView):
    queryset = ApplicationResume.objects.all()
    serializer_class = ApplicationResumeSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticatedStudent]

    def create(self, request, *args, **kwargs):
        resume = request.FILES.get('resume')
        student = request.user.student_profile

        if not resume:
            return Response({"detail": "Resume not provided", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)

        resume_url = upload_file_to_supabase(resume, 'application_resumes/')

        serializer = self.get_serializer(data={'resume': resume_url})
        serializer.is_valid(raise_exception=True)
        serializer.save(student=student)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Internship Applications'], summary='Accept an internship application (alumnus)')
class AcceptInternshipApplicationView(AcceptApplicationView):
    application_model = InternshipApplication
    engagement_model = InternshipEngagement
    engagement_serializer_class = InternshipEngagementSerializer
    validation_serializer_class = AlumnusManageInternshipApplicationSerializer
    relation_name = "internship"


@extend_schema(tags=['Internship Applications'], summary='Reject an internship application (alumnus)')
class RejectInternshipApplicationView(RejectApplicationView):
    validation_serializer_class = AlumnusManageInternshipApplicationSerializer


@extend_schema(tags=['Internship Applications'], summary='Withdraw an internship application (student)')
class WithdrawInternshipApplicationView(WithdrawApplicationView):
    validation_serializer_class = StudentManageInternshipApplicationSerializer
