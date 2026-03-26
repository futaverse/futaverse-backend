from django.core.cache import cache

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .requests import list_banks

class ListBanksView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self):
        cache_key = "paystack_banks_nigeria"
        banks = cache.get(cache_key)
        
        if not banks:
            
            try:
                banks = list_banks()
                cache.set(cache_key, banks, 604800)
                
            except Exception as e:
                return Response({"error": "Failed to fetch banks from payment provider"}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(banks)

class CreateSubaccountView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
