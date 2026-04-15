from django.core.cache import cache
from django.db import transaction

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from .models import Subaccount
from .serializers import ResolveBankAccountSerializer, CreateSubaccountSerializer
from .requests import resolve_bank_account, create_paystack_subaccount, list_banks

@extend_schema(tags=["Payments"], summary="List Paystack Banks and their bank codes")
class ListBanksView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        cache_key = "paystack_banks_nigeria"
        banks = cache.get(cache_key)
        
        if not banks:
            print("Fetching banks from payment provider...")
            try:
                banks = list_banks()
                cache.set(cache_key, banks, 86400) # 24 hours
                
            except Exception as e:
                return Response({"error": "Failed to fetch banks from payment provider"}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(banks)
    
@extend_schema(tags=["Payments"], summary="Check bank account name")
class ResolveAccountView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ResolveBankAccountSerializer
    
    def post(self, request):
        serializer = ResolveBankAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        account_num = serializer.validated_data['account_number']
        bank_code = serializer.validated_data['bank_code']
        bank_name = serializer.validated_data['bank_name']

        try:
            account_name = resolve_bank_account(account_num, bank_code)
            
            cache_key = f"pending_subaccount_{request.user.sqid}"
            
            cache_data = {
                "account_number": account_num,
                "bank_name": bank_name,
                "bank_code": bank_code,
                "account_name": account_name
            }
            cache.set(cache_key, cache_data, timeout=3600) # 1 hour

            return Response({"account_name": account_name}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(tags=["Payments"], summary="Create Paystack subaccount for user after successful account resolution")
class CreateSubaccountView(APIView):
    permission_classes = [IsAuthenticated]
    # serializer_class = CreateSubaccountSerializer

    def post(self, request):
        user = request.user
        
        if Subaccount.objects.filter(user=user).exists():
            return Response({"error": "Subaccount already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        cache_key = f"pending_subaccount_{request.user.sqid}"
        pending_data = cache.get(cache_key)

        if not pending_data:
            return Response(
                {"error": "Verification expired. Please resolve your account again."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                user_data = {
                    "business_name": f"{user.get_full_name()} - YuniVerse",
                    "primary_contact_email": user.email
                }
                
                subaccount_code = create_paystack_subaccount(user_data, pending_data)

                Subaccount.objects.create(
                    user=user,
                    bank_name=pending_data['bank_name'],
                    bank_code=pending_data['bank_code'],
                    account_number=pending_data['account_number'],
                    account_name=pending_data['account_name'],
                    subaccount_code=subaccount_code
                )
                
                transaction.on_commit(lambda: cache.delete(cache_key))
            
            return Response({"message": "Subaccount created successfully!"}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"error": f"Subaccount creation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)