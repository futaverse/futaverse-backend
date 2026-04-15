from rest_framework import serializers

from .models import Subaccount

class ResolveBankAccountSerializer(serializers.Serializer):
    account_number = serializers.CharField()
    bank_code = serializers.CharField()
    bank_name = serializers.CharField()
    
    
class CreateSubaccountSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Subaccount
        fields = ['account_number', 'bank_code', 'bank_name', 'account_name']