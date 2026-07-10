"""
OmniWatch 2.0 — Auth (SSO Provider)
Component: SSOProvider
Layer: Enterprise
Phase: 6
Purpose: OIDC SSO provider with JWT session management (RS256)
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

# RS256 Key Configuration — REQUIRED environment variables
JWT_PRIVATE_KEY = os.environ.get("JWT_PRIVATE_KEY")
JWT_PUBLIC_KEY = os.environ.get("JWT_PUBLIC_KEY")

# Fail fast if keys not configured (except in test mode)
if not JWT_PRIVATE_KEY or not JWT_PUBLIC_KEY:
    if os.getenv("TESTING") != "1":
        raise ValueError(
            "JWT_PRIVATE_KEY and JWT_PUBLIC_KEY environment variables are required. "
            "Generate with: python -c \""
            "from cryptography.hazmat.primitives.asymmetric import rsa; "
            "from cryptography.hazmat.primitives import serialization; "
            "key = rsa.generate_private_key(public_exponent=65537, key_size=2048); "
            "print('JWT_PRIVATE_KEY=' + key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()); "
            "print('JWT_PUBLIC_KEY=' + key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode())"
            "\""
        )
    # Test mode fallback — use symmetric secret for testing only
    JWT_PRIVATE_KEY = os.getenv("JWT_SECRET", "test-secret-key-for-unit-tests")
    JWT_PUBLIC_KEY = JWT_PRIVATE_KEY


class SSOProvider:
    """
    SSO Provider supporting OIDC flow with JWT session management (RS256).
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
        jwt_private_key: Optional[str] = None,
        jwt_public_key: Optional[str] = None,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_db: int = 0,
    ):
        self._jwt_private_key = jwt_private_key or JWT_PRIVATE_KEY
        self._jwt_public_key = jwt_public_key or JWT_PUBLIC_KEY
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

        # RS256: Encode with private key
        access_token = jwt.encode(access_payload, self._jwt_private_key, algorithm="RS256")
        refresh_token = jwt.encode(refresh_payload, self._jwt_private_key, algorithm="RS256")

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

        logger.info("Session created for user %s", user_id)
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
            # RS256: Decode with public key
            payload = jwt.decode(token, self._jwt_public_key, algorithms=["RS256"])
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
        logger.info("Session destroyed for user %s", user_id)
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
            raise ValueError("Unknown provider: %s. Supported: %s" % (provider, list(self.OIDC_ENDPOINTS.keys())))

        client_id = client_id or os.getenv("OIDC_CLIENT_ID", "")

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "state": state,
        }

        endpoint = self.OIDC_ENDPOINTS[provider]
        return "%s?%s" % (endpoint, urlencode(params))


class SAML2Provider:
    """
    SAML2 SSO Provider (fallback when OIDC not configured).
    Provides SAML2 AuthnRequest generation and Response processing.
    """

    def __init__(
        self,
        idp_url: str,
        certificate: str,
        entity_id: str,
        sp_url: str,
    ):
        self.idp_url = idp_url
        self.certificate = certificate
        self.entity_id = entity_id
        self.sp_url = sp_url

    def create_authn_request(self) -> str:
        """
        Generate SAML AuthnRequest XML and return IdP redirect URL.

        Returns:
            IdP URL with SAML AuthnRequest as query parameter.
        """
        import base64
        import zlib

        request_id = "_" + str(uuid.uuid4())
        issue_instant = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        authn_request = """<samlp:AuthnRequest
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="%s"
    Version="2.0"
    IssueInstant="%s"
    Destination="%s"
    AssertionConsumerServiceURL="%s"
    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>%s</saml:Issuer>
    <samlp:NameIDPolicy
        Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
        AllowCreate="true"/>
</samlp:AuthnRequest>""" % (request_id, issue_instant, self.idp_url, self.sp_url, self.entity_id)

        # Base64 encode and deflate
        compressed = zlib.compress(authn_request.encode())[2:-4]
        encoded = base64.b64encode(compressed).decode()

        return "%s?SAMLRequest=%s" % (self.idp_url, encoded)

    def process_saml_response(self, saml_response: str) -> Optional[dict]:
        """
        Process SAML Response from IdP.

        Args:
            saml_response: Base64-encoded SAML Response from IdP.

        Returns:
            dict with user attributes (email, name, groups) or None if invalid.
        """
        import base64
        from xml.etree import ElementTree

        try:
            # Decode and parse
            decoded = base64.b64decode(saml_response)
            root = ElementTree.fromstring(decoded)

            # Extract attributes (simplified — production should validate signature)
            ns = {
                "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
                "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
            }

            # Get subject
            subject = root.find(".//saml:Subject/saml:NameID", ns)
            email = subject.text if subject is not None else ""

            # Get attributes
            attributes = {}
            for attr in root.findall(".//saml:AttributeStatement/saml:Attribute", ns):
                name = attr.get("Name")
                value = attr.find("saml:AttributeValue", ns)
                if name and value is not None:
                    attributes[name] = value.text

            return {
                "email": email,
                "name": attributes.get("displayName", email),
                "groups": attributes.get("groups", "").split(",") if attributes.get("groups") else [],
                "attributes": attributes,
            }
        except Exception as e:
            logger.error("SAML response processing failed: %s", str(e))
            return None
