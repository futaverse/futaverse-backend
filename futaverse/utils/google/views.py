from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from django.shortcuts import redirect
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import logging

from dotenv import load_dotenv
import os

from core.models import User

logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar"
]

google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
google_auth_uri = os.getenv("GOOGLE_AUTH_URI")

def build_google_auth_url(user_id, redirect_after_auth=None):
    return f"{google_auth_uri}?user_id={user_id}&redirect_after_auth={redirect_after_auth}"

def get_google_client_config():
    return {"web": 
            {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uris": [google_redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
    
@extend_schema(
    summary="Initiate Google OAuth flow",
    description="Starts the Google OAuth2 authentication process. Redirects user to Google's consent page.",
    parameters=[
        OpenApiParameter(
            name='user_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description='ID of the user initiating OAuth'
        ),
        OpenApiParameter(
            name='redirect_after_auth',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='URL to redirect to after successful authentication'
        ),
    ],
    responses={
        302: {
            'description': 'Redirect to Google OAuth consent page'
        }
    },
    tags=['Google OAuth']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def google_auth_start(request):
    client_config = get_google_client_config()
    
    user_id = request.query_params.get("user_id")
    user = User.objects.filter(sqid=user_id).first()
    if not user:
        return Response({"detail": "User with provided id not found."}, status=404)

    flow = Flow.from_client_config(client_config, scopes=GOOGLE_SCOPES, redirect_uri=google_redirect_uri)
    
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    
    redirect_after_auth = request.query_params.get("redirect_after_auth", None)
    
    if redirect_after_auth in [None, "", "None", "null"]:
        redirect_after_auth = None

    request.session["google_oauth_state"] = state
    request.session["user_id"] = user_id
    request.session["redirect_after_auth"] = redirect_after_auth

    return redirect(auth_url)

@extend_schema(
    summary="Google OAuth callback",
    description="Callback URL for Google OAuth2 authentication.",
    responses={
        200: {
            'description': 'Authorization successful'
        }
    },
    tags=['Google OAuth']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def google_auth_callback(request):
    state = request.session.get("google_oauth_state")
    user_id = request.session.get("user_id")
    redirect_after_auth = request.session.get("redirect_after_auth", None)
    
    logger.debug(f"state: {state}, user_id: {user_id}, redirect_after_auth: {redirect_after_auth}")
    
    # TODO: Handle errors

    client_config = get_google_client_config()
    flow = Flow.from_client_config(client_config, scopes=GOOGLE_SCOPES, state=state, redirect_uri=google_redirect_uri)
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    creds = flow.credentials

    User.objects.filter(sqid=user_id).update(
        google_credentials={
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }
    )

    if redirect_after_auth:
        return redirect(redirect_after_auth)
    
    return Response({"detail": "Authorization successful, you can exit this page."}, status=status.HTTP_200_OK)
