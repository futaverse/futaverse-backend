from django.urls import path
from .views import VerifySignupOTPView, LoginView, CustomTokenRefreshView, ForgotPasswordView, VerifyForgotPasswordOTPView, ResetPasswordView
from alumnus.views import CreateAlumnusView
from students.views import CreateStudentView


urlpatterns = [
    path('/signup/alumnus', CreateAlumnusView.as_view(), name='create-alumnus'),
    path('/signup/student', CreateStudentView.as_view(), name='create-student'),
    path('/signup/verify-otp', VerifySignupOTPView.as_view(), name='verify-signup-otp'),
    
    path('/login', LoginView.as_view(), name='login'),
    path('/refresh', CustomTokenRefreshView.as_view(), name='refresh'),
    path('/forgot-password/verify-otp', VerifyForgotPasswordOTPView.as_view(), name='verify-forgot-password-otp'),
    
    path('/forgot-password', ForgotPasswordView.as_view(), name='forgot-password'),
    path('/reset-password', ResetPasswordView.as_view(), name='reset-password'),
]