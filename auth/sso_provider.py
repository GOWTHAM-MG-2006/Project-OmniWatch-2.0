"""
OmniWatch 2.0 — Auth (SSO Provider)
Component: SSOProvider
Layer: Enterprise
Phase: 6
Purpose: OIDC SSO provider with JWT session management
Inputs: User credentials, OIDC/SAML2 IdP tokens
Outputs: JWT access/refresh tokens, session management via Redis
"""

import os
import uuid
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import jwt
import redis

logger = logging.getLogger(__name__)


class SSOProvider:
    """
    SSO Provider supporting OIDC flow with JWT session management.
    Provides access/refresh token lifecycle, Redis-backed sessions,
    and OIDC authorization URL generation.
    """

    ACCESS_TOKEN_EXPIRY_MINUTES = 15
    REFRESH_TOKEN_EXPIRY_DAYS = 7

    OIDC_ENDPOINTS = {
        "okta": "https://your-domain.okta.com/oauth2/default/v1/authorize",
        "auth0": "https://your-tenant.auth0.com/authorize",
        "azure": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
        "google": "https://accounts.google.com/o/oauth2/v2/auth",
    }

    def __init__(
        self,
        jwt_secret: Optional[str] = None,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_db: int = 0,
    ):
        self.jwt_secret = jwt_secret or os.getenv("JWT_SECRET", "default-dev-secret-change-in-prod")
        self._redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self._redis_port = redis_port or int(os.getenv("REDIS_PORT", "6379"))
        self._redis_db = redis_db
        self._redis_client: Optional[redis.Redis] = None

    @property
    def redis_client(self) -> redis.Redis:
        """Lazy Redis client initialization."""
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=self._redis_host,
                port=self._redis_port,
                db=self._redis_db,
                decode_responses=True,
            )
        return self._redis_client

    def create_session(
        self,
        user_id: str,
        email: str,
        roles: list[str],
        extra_claims: Optional[dict] = None,
    ) -> dict:
        """
        Create a new session with access and refresh tokens.

        Returns:
            dict with access_token and refresh_token keys.
        """
        now = datetime.now(timezone.utc)

        # Access token (15 min)
        access_payload = {
            "user_id": user_id,
            "email": email,
            "roles": roles,
            "exp": now + timedelta(minutes=self.ACCESS_TOKEN_EXPIRY_MINUTES),
            "iat": now,
            "type": "access",
            "jti": str(uuid.uuid4()),
        }
        if extra_claims:
            access_payload.update(extra_claims)

        # Refresh token (7 days)
        refresh_payload = {
            "user_id": user_id,
            "exp": now + timedelta(days=self.REFRESH_TOKEN_EXPIRY_DAYS),
            "iat": now,
            "type": "refresh",
            "jti": str(uuid.uuid4()),
        }

        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm="HS256")
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm="HS256")

        # Store session in Redis with refresh token expiry
        session_data = {
            "user_id": user_id,
            "email": email,
            "roles": ",".join(roles),
            "refresh_token": refresh_token,
        }
        self.redis_client.setex(
            f"session:{user_id}",
            self.REFRESH_TOKEN_EXPIRY_DAYS * 24 * 3600,
            json.dumps(session_data),
        )

        logger.info(f"Session created for user {user_id}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    def validate_token(self, token: str) -> Optional[dict]:
        """
        Validate a JWT token and return its payload.

        Returns:
            Payload dict if valid, None if invalid/expired.
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            if payload.get("type") not in ("access", "refresh"):
                return None
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[dict]:
        """
        Exchange a valid refresh token for new access + refresh tokens.

        Returns:
            dict with new access_token and refresh_token, or None if invalid.
        """
        payload = self.validate_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload["user_id"]
        session_raw = self.redis_client.get(f"session:{user_id}")
        if not session_raw:
            return None

        # Extract session info (stored as JSON string)
        session_data = json.loads(session_raw)

        return self.create_session(
            user_id=user_id,
            email=session_data.get("email", ""),
            roles=session_data.get("roles", "").split(",") if session_data.get("roles") else [],
        )

    def logout(self, token: str) -> bool:
        """
        Destroy the session associated with the given token.

        Returns:
            True if session destroyed, False if token invalid.
        """
        payload = self.validate_token(token)
        if not payload:
            return False

        user_id = payload["user_id"]
        self.redis_client.delete(f"session:{user_id}")
        logger.info(f"Session destroyed for user {user_id}")
        return True

    def get_oidc_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        provider: str = "google",
        client_id: Optional[str] = None,
        scope: str = "openid profile email",
    ) -> str:
        """
        Generate an OIDC authorization URL for redirect to IdP.

        Args:
            redirect_uri: Callback URL after authentication.
            state: CSRF protection state parameter.
            provider: IdP identifier (okta, auth0, azure, google).
            client_id: OIDC client ID (falls back to env).
            scope: OAuth2 scopes.

        Returns:
            Full authorization URL string.
        """
        if provider not in self.OIDC_ENDPOINTS:
            raise ValueError(f"Unknown provider: {provider}. Supported: {list(self.OIDC_ENDPOINTS.keys())}")

        client_id = client_id or os.getenv("OIDC_CLIENT_ID", "")

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "state": state,
        }

        endpoint = self.OIDC_ENDPOINTS[provider]
        return f"{endpoint}?{urlencode(params)}"
