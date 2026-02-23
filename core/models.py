from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta
from django_sqids import SqidsField

from cloudinary.models import CloudinaryField

from futaverse.utils.generate import generate_otp
from futaverse.models import BaseModel

def default_expiry():
    return timezone.now() + timedelta(minutes=10)

class UserManager(BaseUserManager):
    def create(self, **extra_fields):
        email = extra_fields.get("email")
        password = extra_fields.pop("password", None)
        
        email = self.normalize_email(email)
        user = self.model(**extra_fields)
        if password:
            user.set_password(password)
            
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser):
    class Role(models.TextChoices):
        ALUMNI = 'Alumni', 'alumni'
        STUDENT = 'Student', 'student'
        STAFF = 'Staff', 'staff'
        ADMIN = 'admin', 'Admin'
        
    sqid = SqidsField(real_field_name="id", min_length=7)
    email = models.EmailField(unique=True, blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    
    google_credentials = models.JSONField(null=True, blank=True, default=dict)
    
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    
    objects = UserManager()
    
    def get_profile(self):
        if self.role == self.Role.ALUMNI:
            return getattr(self, 'alumni_profile', None)
        elif self.role == self.Role.STUDENT:
            return getattr(self, 'student_profile', None)
        return None
    
    def get_full_name(self):
        profile = self.get_profile()
        if profile:
            return f"{profile.firstname} {profile.lastname}"
        return self.email
    
    def __str__(self):
        return f"{self.email} ({self.role})"
    
class OTP(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="otp")
    otp = models.CharField(max_length=6)  
    expiry = models.DateTimeField(default=default_expiry)
    verified = models.BooleanField(default=False)
    
    @classmethod
    def generate_otp(cls, user, expiry_minutes=10):
        """Create or replace OTP for a user"""
        otp = generate_otp()
        expiry_time = timezone.now() + timedelta(minutes=expiry_minutes)

        otp, _ = cls.objects.update_or_create(
            user=user,
            defaults={
                "otp": otp,
                "expiry": expiry_time,
                "verified": False
            }
        )
        return otp

    def is_expired(self):
        return timezone.now() > self.expiry

    def verify(self, otp):
        if self.verified:
            return False, "OTP already used"

        if self.is_expired():
            return False, "This OTP has expired"

        if self.otp != otp:
            return False, "Invalid OTP"

        self.verified = True
        self.save(update_fields=["verified"])
        return True, "OTP verified successfully"
    
    def __str__(self):
        return self.otp
    
class UserProfileImage(BaseModel):
    user = models.ForeignKey(User, related_name="profile_img", on_delete=models.SET_NULL, null=True, blank=True)
    image = CloudinaryField("profile_images/") 
    uploaded_at = models.DateTimeField(auto_now_add=True)
