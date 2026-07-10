"""
OmniWatch 2.0 — NexusUX
Component: Auth Route
Layer: 11
Phase: 6
Purpose: API endpoints for SSO login, callback, and logout
Inputs: HTTP requests (SSO code, session tokens)
Outputs: JWT tokens, session management
"""

import uuid
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from auth.sso_provider import SSOProvider

router = APIRouter()
sso = SSOProvider()


@router.get("/login")
async def login(provider: str = "google"):
    """Redirect to SSO provider for authentication."""
    state = str(uuid.uuid4())
    redirect_uri = "http://localhost:8000/api/v1/auth/callback"
    auth_url = sso.get_oidc_authorization_url(
        redirect_uri=redirect_uri,
        state=state,
        provider=provider,
    )
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(code: str, state: str):
    """Handle SSO callback — exchange code for token.

    In production, this would exchange the authorization code with the IdP
    for tokens. For now, it returns a placeholder indicating the flow is
    acknowledged.
    """
    return {
        "status": "callback_received",
        "code": code,
        "state": state,
        "message": "SSO callback processed. In production, tokens would be issued here.",
    }


@router.post("/logout")
async def logout(request: Request):
    """Destroy the current user session."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    if not token:
        return {"status": "error", "message": "No token provided"}

    success = sso.logout(token)
    if success:
        return {"status": "logged_out"}
    return {"status": "error", "message": "Invalid or expired token"}
