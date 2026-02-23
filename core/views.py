from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.generics import GenericAPIView

from drf_spectacular.utils import extend_schema

from .models import User, OTP, UserProfileImage
from .serializers import UserProfileImageSerializer, VerifyOTPSerializer, ForgotPasswordSerializer, ResetPasswordSerializer

from futaverse.views import PublicGenericAPIView
from futaverse.utils.email_service import BrevoEmailService

mailer = BrevoEmailService()

def set_refresh_cookie(response):
    data = response.data
    refresh = data.get("refresh")
    access = data.get("access")

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,    
        secure=True,      
        samesite="None"
    )

    response.data = {"data": {"access_token": access}, "detail": "Access granted", "status": "success"}
            
    return response

@extend_schema(tags=['Users'])
class UploadUserProfileImageView(generics.CreateAPIView, PublicGenericAPIView):
    queryset = UserProfileImage.objects.all()
    serializer_class = UserProfileImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    
@extend_schema(tags=['Auth'])
class VerifySignupOTPView(PublicGenericAPIView):  
    serializer_class = VerifyOTPSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        valid, message = serializer.otp_instance.verify(serializer.otp)
        if not valid:
            return Response({"detail": message, "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.user.is_active = True
        serializer.user.save(update_fields=['is_active'])
        
        return Response({"detail": f"Email verified successfully, proceed to login"}, status=status.HTTP_200_OK)

@extend_schema(tags=['Auth'])
class LoginView(TokenObtainPairView, PublicGenericAPIView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        mailer.send(
            subject="New Login Alert",
            body = "There was a login attempt on your FutaVerse account. If this was you, you can ignore this message. \n\nIf this was not you, please contact our support team at ....................com \n\n\nFrom the FutaVerse Team",
            recipient=request.data.get("email"),         
        )
        
        if response.status_code == status.HTTP_200_OK:
            set_refresh_cookie(response)
            
            user = User.objects.get(email=request.data.get("email"))
            role = user.role
            sqid = user.get_profile().sqid
            print(user, role)
            
            response.data["data"]["role"] = role
            response.data["data"]["sqid"] = sqid
            
        return response

@extend_schema(tags=['Auth'])
class TokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        
        if not refresh_token:
            return Response({"detail": "Session timeout, please login again"}, status=400)

        request.data["refresh"] = refresh_token
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            set_refresh_cookie(response)
        
        return response
    
@extend_schema(tags=['Auth'])
class ForgotPasswordView(PublicGenericAPIView):
    serializer_class = ForgotPasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        otp = OTP.generate_otp(serializer.user)
        print(otp)
        
        mailer.send(
            subject="Account Recovery",
            body= (
                        f"Enter the OTP below into the required field \n"
                        f"The OTP will expire in 10 mins\n\n"
                        f"OTP: {otp} \n\n"
                        f"If you did not iniate this request, please contact our support team at ..............com   \n\n\n"
                        f"From the Docuhealth Team"
                    ),
            recipient=serializer.email,
        )
        
        return Response({"detail": f"OTP sent successfully"}, status=status.HTTP_200_OK)
    
@extend_schema(tags=['Auth'])
class VerifyForgotPasswordOTPView(PublicGenericAPIView):
    serializer_class = VerifyOTPSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        valid, message = serializer.otp_instance.verify(serializer.otp)
        if not valid:
            return Response({"detail": message, "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        access = AccessToken.for_user(serializer.user)

        return Response({"data": {"access_token": str(access)}, "detail": "Access granted to reset password", "status": "success"}, status=status.HTTP_200_OK,)

@extend_schema(tags=['Auth'])  
class ResetPasswordView(GenericAPIView):
    serializer_class = ResetPasswordSerializer
    
    def patch(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_password = serializer.validated_data["new_password"]

        user = request.user
        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password reset successfully. Please log in with your new credentials.", "status": "success"}, status=200)
    
    


    
