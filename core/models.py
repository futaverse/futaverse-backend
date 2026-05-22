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
        ALUMNI = 'alumni', 'Alumni'
        STUDENT = 'student', 'Student'
        STAFF = 'staff', 'Staff'
        ADMIN = 'admin', 'Admin'
        
    PROFILE_RELATIONS = {
        Role.ALUMNI: "alumni_profile",
        Role.STUDENT: "student_profile",
    }
        
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
    
    @property
    def profile(self):
        relation = self.PROFILE_RELATIONS.get(self.role)

        if not relation:
            return None

        return getattr(self, relation, None)
    
    def get_full_name(self):
        profile = self.profile()
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
    
class LevelChoices(models.IntegerChoices):
    LEVEL_100 = 100, "100"
    LEVEL_200 = 200, "200"
    LEVEL_300 = 300, "300"
    LEVEL_400 = 400, "400"
    LEVEL_500 = 500, "500"
    LEVEL_600 = 600, "600"
    LEVEL_700 = 700, "700"

class StudentProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    
    class Gender(models.TextChoices):
        MALE = 'Male', 'male'
        FEMALE = 'Female', 'female'
        OTHER = 'Other', 'other'
        UNKNOWN = 'Unknown', 'unknown'
        
    phone_num = models.CharField()
    gender = models.CharField(choices=Gender.choices)
        
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True)
    
    address = models.CharField(max_length=255)
    state = models.CharField(max_length=20)
    country = models.CharField(max_length=20)
    
    description = models.TextField(blank=True, null=True)
    
    matric_no = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=30)
    faculty = models.CharField(max_length=60)
    level = models.IntegerField(choices=LevelChoices.choices)
    cgpa = models.DecimalField(max_digits=3, decimal_places=2)
    skills = models.JSONField(default=list) # TODO: Make this a drop down on the frontend
    expected_grad_year = models.CharField(max_length=4)
    
    preferred_industry = models.CharField(blank=True, null=True)
    preferred_company_type = models.CharField(blank=True, null=True)
    # willingness_to_relocate = models.BooleanField()
    willingness_to_be_mentored = models.BooleanField(default=True)
    
    linkedin_url = models.URLField(blank=True, null=True, max_length=200)
    github_url = models.URLField(blank=True, null=True, max_length=200)
    website_url = models.URLField(blank=True, null=True, max_length=200)
    x_url = models.URLField(blank=True, null=True, max_length=200)
    instagram_url = models.URLField(blank=True, null=True, max_length=200)
    facebook_url = models.URLField(blank=True, null=True, max_length=200)
    
    @property
    def full_name(self):
        return f"{self.firstname} {self.lastname}"
    
    def __str__(self):
        return f"{self.full_name} (student)"
    
    @property
    def feed_match_filter(self):
        attributes = []

        for skill in self.skills: 
            attributes.append(models.Q(targets__target_type='skill', targets__target_value=skill))

        if self.department:
            attributes.append(models.Q(targets__target_type='department', targets__target_value=self.department))
            
        if self.faculty:
            attributes.append(models.Q(targets__target_type='faculty', targets__target_value=self.faculty))

        if self.level:
            attributes.append(models.Q(targets__target_type='level', targets__target_value=str(self.level)))
            
        if self.preferred_industry:
            attributes.append(models.Q(targets__target_type='industry', targets__target_value=self.preferred_industry))
            
        if self.preferred_company_type:
            attributes.append(models.Q(targets__target_type='company_type', targets__target_value=self.preferred_company_type))

        if not attributes:
            return None

        match_filter = attributes[0]
        for attr in attributes[1:]:
            match_filter |= attr

        return match_filter
    
class StudentResume(BaseModel):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='resume', blank=True, null=True)
    resume = models.URLField(max_length=200)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Resume of {self.student.full_name} uploaded at {self.uploaded_at}"
    
class AlumniProfile(BaseModel):
    class Gender(models.TextChoices):
        MALE = 'Male', 'male'
        FEMALE = 'Female', 'female'
        OTHER = 'Other', 'other'
        UNKNOWN = 'Unknown', 'unknown'
        
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="alumni_profile")
    
    phone_num = models.CharField()
    gender = models.CharField(choices=Gender.choices)
        
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True)
    
    address = models.CharField(max_length=255)
    state = models.CharField(max_length=20)
    country = models.CharField(max_length=20)
    
    description = models.TextField(blank=True, null=True)
    
    matric_no = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=30)
    faculty = models.CharField(max_length=20)
    grad_year = models.CharField(max_length=4)
    
    current_job_title = models.CharField()
    current_company = models.CharField() # TODO: Add company type
    industry = models.CharField()
    years_of_exp = models.IntegerField()
    previous_comps = models.JSONField(default=list, blank=True, null=True)
    
    linkedin_url = models.URLField(blank=True, null=True, max_length=200)
    company_linkedin_url = models.URLField(blank=True, null=True, max_length=200)
    github_url = models.URLField(blank=True, null=True, max_length=200)
    website_url = models.URLField(blank=True, null=True, max_length=200)
    company_website_url = models.URLField(blank=True, null=True, max_length=200)
    x_url = models.URLField(blank=True, null=True, max_length=200)
    instagram_url = models.URLField(blank=True, null=True, max_length=200)
    facebook_url = models.URLField(blank=True, null=True, max_length=200)
    
    @property
    def full_name(self):
        return f"{self.firstname} {self.lastname}"
    
    def __str__(self):
        return f"{self.full_name} (alumnus)"
    
    @property
    def feed_match_filter(self):
        attributes = []

        if self.department:
            attributes.append(models.Q(targets__target_type='department', targets__target_value=self.department))
            
        if self.faculty:
            attributes.append(models.Q(targets__target_type='faculty', targets__target_value=self.faculty))

        if self.industry:
            attributes.append(models.Q(targets__target_type='industry', targets__target_value=self.industry))
            
        # if self.company_type:
        #     attributes.append(models.Q(targets__target_type='company_type', targets__target_value=self.company_type))

        if not attributes:
            return None

        match_filter = attributes[0]
        for attr in attributes[1:]:
            match_filter |= attr

        return match_filter
