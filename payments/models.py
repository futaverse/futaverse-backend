from django.db import models

from core.models import User
from futaverse.models import BaseModel

class Subaccount(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="account_details")
    
    bank_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=10)  
    account_number = models.CharField(max_length=10)
    account_name = models.CharField(max_length=255)
    
    subaccount_code = models.CharField(max_length=100, unique=True, help_text="The ACCT_xxxx code from Paystack")
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.account_name} - {self.subaccount_code}"