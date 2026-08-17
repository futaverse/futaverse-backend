import logging
import os

from django.shortcuts import redirect
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.models import User

logger = logging.getLogger(__name__)

load_dotenv()


GOOGLE_LOGIN_SCOPES = ["openid", "email", "profile"]


@api_view(["GET"])
@permission_classes([AllowAny])
def google_login_start(request):
    try:
        client_config = get_google_client_config()

        flow = Flow.from_client_config(
            client_config,
            scopes=GOOGLE_LOGIN_SCOPES,
            redirect_uri=google_login_redirect_uri,  # separate redirect URI from calendar flow
        )

        auth_url, state = flow.authorization_url(
            include_granted_scopes="true",
            prompt="select_account",
        )

        redirect_after_auth = request.query_params.get("redirect_after_auth", None)
        if redirect_after_auth in [None, "", "None", "null"]:
            redirect_after_auth = None

        request.session["google_login_state"] = state
        request.session["login_redirect_after_auth"] = redirect_after_auth

        return redirect(auth_url)

    except Exception as e:
        logger.error(f"Error starting Google login flow: {e}")
        return Response(
            {"error": "Something went wrong. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def google_login_callback(request):
    try:
        state = request.session.get("google_login_state")
        redirect_after_auth = request.session.get("login_redirect_after_auth", None)

        if not state:
            return Response({"detail": "Session expired or invalid."}, status=400)

        returned_state = request.query_params.get("state")
        if not returned_state or returned_state != state:
            logger.warning("Google login state mismatch. Possible CSRF attempt.")
            return Response({"detail": "Invalid OAuth state."}, status=400)

        client_config = get_google_client_config()
        flow = Flow.from_client_config(
            client_config,
            scopes=GOOGLE_LOGIN_SCOPES,
            state=state,
            redirect_uri=google_login_redirect_uri,
        )
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        creds = flow.credentials

        # Verify + decode the ID token to get identity claims
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token

        id_info = google_id_token.verify_oauth2_token(
            creds.id_token, google_requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
        )

        email = id_info["email"]
        google_sub = id_info["sub"]
        name = id_info.get("name", "")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"name": name, "google_sub": google_sub},
        )
        if not created and not user.google_sub:
            user.google_sub = google_sub
            user.save(update_fields=["google_sub"])

        # Issue your own session/JWT here — depends on what DocuHealth uses for auth
        # e.g. refresh, access = get_tokens_for_user(user)

        if redirect_after_auth:
            separator = "&" if "?" in redirect_after_auth else "?"
            return redirect(f"{redirect_after_auth}{separator}token={access}")

        return Response({"detail": "Login successful"}, status=200)

    except Exception as e:
        logger.error(f"Error processing Google login callback: {e}")
        return Response(
            {"error": "Something went wrong. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
