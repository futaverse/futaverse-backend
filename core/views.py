import logging

from django.db import transaction
from django_filters import rest_framework as filters
from drf_spectacular.utils import (
    OpenApiExample,
    PolymorphicProxySerializer,
    extend_schema,
)
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from futaverse.permissions import IsAuthenticatedStudent
from futaverse.utils.email_service import BrevoEmailService
from futaverse.utils.supabase import upload_file_to_supabase
from futaverse.views import PublicGenericAPIView

from .filters import UserSearchFilter
from .models import OTP, StudentResume, User, UserProfileImage
from .serializers import (
    AlumniMeResponseSerializer,
    CreateAlumnusSerializer,
    CreateStudentSerializer,
    ForgotPasswordSerializer,
    MeSerializer,
    PersonSearchResultSerializer,
    ResetPasswordSerializer,
    StudentMeResponseSerializer,
    StudentResumeSerializer,
    UserProfileImageSerializer,
    VerifyOTPSerializer,
)

mailer = BrevoEmailService()
logger = logging.getLogger(__name__)

MAX_RESUME_SIZE = 5 * 1024 * 1024


def set_refresh_cookie(response):
    data = response.data
    refresh = data.get("refresh")
    access = data.get("access")

    response.set_cookie(
        key="refresh_token", value=refresh, httponly=True, secure=True, samesite="None"
    )

    response.data = {
        "data": {"access_token": access},
        "detail": "Access granted",
        "status": "success",
    }

    return response


@extend_schema(tags=["Users"])
class UploadUserProfileImageView(generics.CreateAPIView, PublicGenericAPIView):
    queryset = UserProfileImage.objects.all()
    serializer_class = UserProfileImageSerializer
    parser_classes = [MultiPartParser, FormParser]


@extend_schema(tags=["Auth"])
class VerifySignupOTPView(PublicGenericAPIView):
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        valid, message = serializer.otp_instance.verify(serializer.otp)
        if not valid:
            return Response(
                {"detail": message, "status": "error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.user.is_active = True
        serializer.user.save(update_fields=["is_active"])

        return Response(
            {"detail": "Email verified successfully, proceed to login"},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Auth"])
class LoginView(TokenObtainPairView, PublicGenericAPIView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        mailer.send(
            subject="New Login Alert",
            body="There was a login attempt on your FutaVerse account. If this was you, you can ignore this message. \n\nIf this was not you, please contact our support team at futaverseedu@gmail.com \n\n\nFrom the FutaVerse Team",
            recipient=request.data.get("email"),
        )

        if response.status_code == status.HTTP_200_OK:
            set_refresh_cookie(response)

            user = User.objects.get(email=request.data.get("email"))
            role = user.role
            user_sqid = user.sqid
            sqid = user.profile.sqid

            response.data["data"]["role"] = role
            response.data["data"]["user_sqid"] = user_sqid
            response.data["data"]["sqid"] = sqid

        return response


ME_RESPONSES = {
    200: PolymorphicProxySerializer(
        component_name="MeResponse",
        serializers=[StudentMeResponseSerializer, AlumniMeResponseSerializer],
        resource_type_field_name="role",
    )
}

ME_EXAMPLES = [
    OpenApiExample(
        name="Student response",
        response_only=True,
        value={
            "data": {
                "sqid": "user-sqid",
                "email": "student@test.com",
                "role": "student",
                "created_at": "2026-01-01T00:00:00Z",
                "profile": {
                    "sqid": "profile-sqid",
                    "phone_num": "08012345678",
                    "gender": "male",
                    "firstname": "Test",
                    "lastname": "Student",
                    "middlename": "",
                    "address": "123 Test St",
                    "state": "Lagos",
                    "country": "Nigeria",
                    "description": None,
                    "matric_no": "FUTA/20/0001",
                    "department": "Computer Science",
                    "faculty": "Engineering",
                    "level": 300,
                    "cgpa": "4.50",
                    "skills": ["python", "django"],
                    "expected_grad_year": "2027",
                    "preferred_industry": None,
                    "preferred_company_type": None,
                    "willingness_to_be_mentored": True,
                    "linkedin_url": None,
                    "github_url": None,
                    "website_url": None,
                    "x_url": None,
                    "instagram_url": None,
                    "facebook_url": None,
                    "avg_rating": None,
                    "total_reviews": 0,
                    "created_at": "2026-01-01T00:00:00Z",
                    "profile_img_url": "https://res.cloudinary.com/example/student.jpg",
                    "resumes": [
                        {
                            "sqid": "resume-sqid",
                            "resume": "https://example.com/resume.pdf",
                            "filename": "cv.pdf",
                            "uploaded_at": "2026-01-02T00:00:00Z",
                        }
                    ],
                },
            },
            "status": "success",
        },
    ),
    OpenApiExample(
        name="Alumni response",
        response_only=True,
        value={
            "data": {
                "sqid": "user-sqid",
                "email": "alumnus@test.com",
                "role": "alumni",
                "created_at": "2026-01-01T00:00:00Z",
                "profile": {
                    "sqid": "profile-sqid",
                    "phone_num": "08098765432",
                    "gender": "male",
                    "firstname": "Test",
                    "lastname": "Alumnus",
                    "middlename": "",
                    "address": "456 Test Ave",
                    "state": "Ogun",
                    "country": "Nigeria",
                    "description": None,
                    "matric_no": "FUTA/14/0002",
                    "department": "Computer Science",
                    "faculty": "Engineering",
                    "grad_year": "2020",
                    "current_job_title": "Software Engineer",
                    "current_company": "Tech Corp",
                    "industry": "Technology",
                    "years_of_exp": 5,
                    "previous_comps": ["Startup Inc"],
                    "linkedin_url": None,
                    "company_linkedin_url": None,
                    "github_url": None,
                    "website_url": None,
                    "company_website_url": None,
                    "x_url": None,
                    "instagram_url": None,
                    "facebook_url": None,
                    "avg_rating": None,
                    "total_reviews": 0,
                    "created_at": "2026-01-01T00:00:00Z",
                    "profile_img_url": "https://res.cloudinary.com/example/alumnus.jpg",
                },
            },
            "status": "success",
        },
    ),
]


@extend_schema(
    tags=["Auth"],
    summary="Get current user profile",
    description="Returns the authenticated user's information including their role-specific profile.",
    responses=ME_RESPONSES,
    examples=ME_EXAMPLES,
)
class MeView(generics.GenericAPIView):
    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = self.get_serializer(request.user)
        return Response({"data": serializer.data, "status": "success"})


@extend_schema(tags=["Auth"])
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"detail": "Session timeout, please login again"}, status=400
            )

        request.data["refresh"] = refresh_token
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            set_refresh_cookie(response)

        return response


@extend_schema(tags=["Auth"])
class ForgotPasswordView(PublicGenericAPIView):
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = OTP.generate_otp(serializer.user)

        try:
            mailer.send(
                subject="Account Recovery",
                body=(
                    f"Enter the OTP below into the required field \n"
                    f"The OTP will expire in 10 mins\n\n"
                    f"OTP: {otp} \n\n"
                    f"If you did not initiate this request, please contact our support team at futaverseedu@gmail.com   \n\n\n"
                    f"From the FutaVerse Team"
                ),
                recipient=serializer.email,
            )
        except Exception as e:
            logger.warning(
                "Email send failed during forgot-password for %s: %s",
                serializer.email,
                e,
            )

        return Response({"detail": "OTP sent successfully"}, status=status.HTTP_200_OK)


@extend_schema(tags=["Auth"])
class VerifyForgotPasswordOTPView(PublicGenericAPIView):
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        valid, message = serializer.otp_instance.verify(serializer.otp)
        if not valid:
            return Response(
                {"detail": message, "status": "error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access = AccessToken.for_user(serializer.user)

        return Response(
            {
                "data": {"access_token": str(access)},
                "detail": "Access granted to reset password",
                "status": "success",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Auth"])
class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer

    def patch(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data["new_password"]

        user = request.user
        user.set_password(new_password)
        user.save()

        return Response(
            {
                "detail": "Password reset successfully. Please log in with your new credentials.",
                "status": "success",
            },
            status=200,
        )


@extend_schema(tags=["Auth"])
class CreateStudentView(generics.CreateAPIView, PublicGenericAPIView):
    serializer_class = CreateStudentSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")

        existing_inactive_user = User.objects.filter(
            email=email, is_active=False
        ).first()
        if existing_inactive_user:
            existing_inactive_user.delete()

        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        with transaction.atomic():
            user = serializer.save()
            otp = OTP.generate_otp(user)

        try:
            mailer.send(
                subject="Verify your email",
                body=(
                    f"Enter the OTP below into the required field \n"
                    f"The OTP will expire in 10 mins\n\n"
                    f"OTP: {otp}\n\n"
                    f"If you did not initiate this request, please contact futaverseedu@gmail.com\n\n"
                    f"From the FutaVerse Team"
                ),
                recipient=user.email,
            )
        except Exception as e:
            logger.warning("Email send failed during signup for %s: %s", user.email, e)


@extend_schema(tags=["Students"])
class ListStudentResumesView(generics.ListAPIView):
    serializer_class = StudentResumeSerializer
    permission_classes = [IsAuthenticatedStudent]

    def get_queryset(self):
        return StudentResume.objects.filter(
            student=self.request.user.student_profile
        ).order_by("-uploaded_at")


@extend_schema(tags=["Students"])
class UploadStudentResumeView(generics.CreateAPIView):
    queryset = StudentResume.objects.all()
    serializer_class = StudentResumeSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticatedStudent]

    def create(self, request, *args, **kwargs):
        student = request.user.student_profile
        resume = request.FILES.get("resume")

        if not resume:
            return Response(
                {"detail": "Resume not provided", "status": "error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not resume.name.lower().endswith(".pdf"):
            return Response(
                {"detail": "Only PDF files are allowed", "status": "error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if resume.size > MAX_RESUME_SIZE:
            return Response(
                {"detail": "Resume must be 5MB or less", "status": "error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        public_url = upload_file_to_supabase(resume, f"resumes/{student.id}")

        serializer = self.get_serializer(
            data={"resume": public_url, "filename": resume.name}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(student=student)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Students"])
class DeleteStudentResumeView(generics.DestroyAPIView):
    serializer_class = StudentResumeSerializer
    permission_classes = [IsAuthenticatedStudent]
    lookup_field = "sqid"

    def get_queryset(self):
        return StudentResume.objects.filter(student=self.request.user.student_profile)

    def perform_destroy(self, instance):
        instance.soft_delete()


@extend_schema(tags=["Auth"])
class CreateAlumnusView(generics.CreateAPIView, PublicGenericAPIView):
    serializer_class = CreateAlumnusSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")

        existing_inactive_user = User.objects.filter(
            email=email, is_active=False
        ).first()
        if existing_inactive_user:
            existing_inactive_user.delete()

        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = serializer.save()
        otp = OTP.generate_otp(user)

        mailer.send(
            subject="Verify your email",
            body=(
                f"Enter the OTP below into the required field \n"
                f"The OTP will expire in 10 mins\n\n"
                f"OTP: {otp}\n\n"
                f"If you did not initiate this request, please contact futaverseedu@gmail.com\n\n"
                f"From the FutaVerse Team"
            ),
            recipient=user.email,
        )


@extend_schema(tags=["Core"], summary="Search people by name and role")
class SearchPeopleView(generics.ListAPIView):
    serializer_class = PersonSearchResultSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = UserSearchFilter

    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        role = self.request.query_params.get("role")

        if role == User.Role.ALUMNI:
            return User.objects.filter(role=role).select_related("alumni_profile")

        return User.objects.filter(role=role).select_related("student_profile")
