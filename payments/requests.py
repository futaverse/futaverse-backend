import os
import requests
from dotenv import load_dotenv

load_dotenv()

paystack_key = os.getenv('PAYSTACK_TEST_SECRET_KEY')

headers = {
                "Authorization": f"Bearer {paystack_key}",
                "Content-Type": "application/json"
            }

base_url = "https://api.paystack.co/"

def send_paystack_request(method, url, payload=None):
        response = requests.request(method, f'{base_url}{url}', json=payload, headers=headers)
        return response
    
def initialize_transaction(payload): # amount in kobo, email, customer_code, reference
    response = send_paystack_request("POST", "transaction/initialize", payload)
    response_data = response.json()
    
    print(response_data)
    
    if response.ok and response_data.get("status"):
        return response_data["data"]["authorization_url"]
    
    raise Exception(response_data.get("message", "Failed to initialize Paystack transaction"))

def list_banks():
    path = f"bank?country=nigeria"
    response = send_paystack_request("GET", path)
    response_data = response.json()
    
    if response.ok and response_data.get("status"):
        banks = response_data["data"]
        filtered_banks = [
            {"name": bank["name"], "code": bank["code"]}
            for bank in banks
            if bank["active"] and bank["supports_transfer"] and bank["country"] == "Nigeria"
        ]
        return filtered_banks
    
    raise Exception(response_data.get("message", "Failed to list Paystack banks"))

def create_paystack_subaccount(user_data, account_data): # bank_code, account_number
    payload = {
        "settlement_bank": account_data['bank_code'],
        "account_number": account_data['account_number'],
        "percentage_charge": 95.5, # We take 4.5% fee
        "business_name": user_data["business_name"],
        "primary_contact_email": user_data["primary_contact_email"]
    }
    
    response = send_paystack_request("POST", "subaccount", payload)
    response_data = response.json()
    
    if response.ok and response_data.get("status"):
        return response_data["data"]["subaccount_code"]
    
    raise Exception(response_data.get("message", "Failed to create Paystack subaccount"))

def resolve_bank_account(account_number, bank_code):
    path = f"bank/resolve?account_number={account_number}&bank_code={bank_code}"
    
    response = send_paystack_request("GET", path)
    response_data = response.json()
    
    if response.ok and response_data.get("status"):
        print(response_data['data'])
        return response_data['data']['account_name']
    
    raise Exception(response_data.get("message", "Could not verify account details."))