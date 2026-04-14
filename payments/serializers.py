from rest_framework import serializers

class ResolveBankAccountSerializer(serializers.Serializer):
    account_number = serializers.CharField()
    bank_code = serializers.CharField()
    bank_name = serializers.CharField()
    
    
# class CreateSubaccountSerializer(serializers.ModelSerializer):
    
#     class Meta:
#         model = 