from django.db import models
from core.models import User
from futaverse.models import BaseModel

class AlumniProfile(BaseModel):
    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'
        UNKNOWN = 'unknown', 'Unknown'
        
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
    current_company = models.CharField()
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
    