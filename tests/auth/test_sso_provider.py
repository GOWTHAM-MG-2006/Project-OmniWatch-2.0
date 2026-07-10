"""
OmniWatch 2.0 — Auth (SSO Provider)
Component: SSOProvider Tests
Layer: Enterprise
Phase: 6
Purpose: Tests for OIDC SSO provider with JWT session management
Inputs: Mock Redis, mock JWT tokens
Outputs: Test assertions for session lifecycle
"""

import jwt
import json
import pytest
from unittest.mock import MagicMock, patch

from auth.sso_provider import SSOProvider


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = MagicMock()
    mock.setex.return_value = True
    mock.get.return_value = None
    mock.delete.return_value = 1
    mock.ping.return_value = True
    return mock


@pytest.fixture
def provider(mock_redis):
    """SSOProvider with mocked Redis."""
    p = SSOProvider(
        jwt_secret="test-secret-key-for-unit-tests",
        redis_host="localhost",
        redis_port=6379
    )
    p._redis_client = mock_redis
    return p


class TestCreateSession:
    """Tests for session creation."""

    def test_create_session_returns_tokens(self, provider, mock_redis):
        result = provider.create_session(
            user_id="user-123",
            email="test@example.com",
            roles=["admin", "viewer"]
        )

        assert "access_token" in result
        assert "refresh_token" in result
        assert isinstance(result["access_token"], str)
        assert isinstance(result["refresh_token"], str)

    def test_create_session_stores_in_redis(self, provider, mock_redis):
        provider.create_session(
            user_id="user-456",
            email="admin@example.com",
            roles=["admin"]
        )

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "session:user-456"
        assert call_args[0][1] == 604800  # 7 days in seconds


class TestValidateToken:
    """Tests for token validation."""

    def test_validate_token_valid(self, provider):
        result = provider.create_session(
            user_id="user-789",
            email="valid@example.com",
            roles=["user"]
        )

        payload = provider.validate_token(result["access_token"])

        assert payload is not None
        assert payload["user_id"] == "user-789"
        assert payload["email"] == "valid@example.com"
        assert "roles" in payload
        assert payload["roles"] == ["user"]

    def test_validate_token_invalid(self, provider):
        payload = provider.validate_token("invalid.token.here")
        assert payload is None

    def test_validate_token_expired(self, provider):
        from datetime import datetime, timedelta

        expired_payload = {
            "user_id": "user-expired",
            "email": "expired@example.com",
            "roles": ["user"],
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(hours=2),
            "type": "access"
        }

        expired_token = jwt.encode(
            expired_payload,
            provider.jwt_secret,
            algorithm="HS256"
        )

        payload = provider.validate_token(expired_token)
        assert payload is None


class TestRefreshToken:
    """Tests for token refresh."""

    def test_refresh_valid_token(self, provider, mock_redis):
        result = provider.create_session(
            user_id="user-refresh",
            email="refresh@example.com",
            roles=["viewer"]
        )

        # Simulate Redis returning the stored session data for this user
        session_data = json.dumps({
            "user_id": "user-refresh",
            "email": "refresh@example.com",
            "roles": "viewer",
            "refresh_token": result["refresh_token"],
        })
        mock_redis.get.return_value = session_data

        new_tokens = provider.refresh_access_token(result["refresh_token"])

        assert new_tokens is not None
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["access_token"] != result["access_token"]

    def test_refresh_invalid_token(self, provider):
        result = provider.refresh_access_token("invalid.refresh.token")
        assert result is None


class TestLogout:
    """Tests for session logout."""

    def test_logout_destroys_session(self, provider, mock_redis):
        result = provider.create_session(
            user_id="user-logout",
            email="logout@example.com",
            roles=["user"]
        )

        logout_result = provider.logout(result["access_token"])

        assert logout_result is True
        mock_redis.delete.assert_called_once_with("session:user-logout")

    def test_logout_invalid_token(self, provider, mock_redis):
        logout_result = provider.logout("invalid.token.here")
        assert logout_result is False
        mock_redis.delete.assert_not_called()


class TestOIDC:
    """Tests for OIDC authorization URL generation."""

    def test_get_oidc_authorization_url(self, provider):
        url = provider.get_oidc_authorization_url(
            redirect_uri="https://app.example.com/callback",
            state="random-state-value"
        )

        assert "https://accounts.google.com/o/oauth2/v2/auth" in url
        assert "redirect_uri=" in url
        assert "state=random-state-value" in url
        assert "response_type=code" in url
        assert "scope=openid" in url
