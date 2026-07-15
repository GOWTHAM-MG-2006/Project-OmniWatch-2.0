"""
OmniWatch 2.0 — Auth (Middleware)
Component: Auth Middleware Tests
Layer: Enterprise
Phase: 6
Purpose: Tests for FastAPI auth middleware — validates TESTING bypass behavior
Inputs: FastAPI test client
Outputs: Test assertions for auth bypass in development mode
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

# TESTING=1 activates the auth bypass — all requests return 200 with test-user
os.environ["TESTING"] = "1"

import importlib
import auth.middleware
importlib.reload(auth.middleware)
from auth.middleware import require_auth


@pytest.fixture
def app():
    """FastAPI test app with auth-protected endpoint."""
    test_app = FastAPI()

    @test_app.get("/protected")
    async def protected_endpoint(
        user=Depends(require_auth("incidents", "read")),
    ):
        return {"message": "success", "user": user}

    yield test_app


class TestTestingBypass:
    """Tests that TESTING=1 bypass returns 200 for all requests."""

    def test_no_token_returns_200(self, app):
        """No Authorization header → 200 (bypass active)."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/protected")
        assert response.status_code == 200
        assert response.json()["user"]["user_id"] == "test-user"

    def test_malformed_token_returns_200(self, app):
        """Invalid token format → 200 (bypass active)."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/protected", headers={"Authorization": "Bearer invalid.token.here"})
        assert response.status_code == 200
        assert response.json()["user"]["user_id"] == "test-user"

    def test_expired_token_returns_200(self, app):
        """Expired JWT → 200 (bypass active)."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/protected", headers={"Authorization": "Bearer expired.jwt.token"})
        assert response.status_code == 200

    def test_malformed_auth_header_returns_200(self, app):
        """Missing 'Bearer' prefix → 200 (bypass active)."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/protected", headers={"Authorization": "Token some-token"})
        assert response.status_code == 200

    def test_valid_jwt_returns_200(self, app):
        """Valid JWT → 200 (bypass active)."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/protected", headers={"Authorization": "Bearer some.jwt.token"})
        assert response.status_code == 200
        assert response.json()["user"]["user_id"] == "test-user"

    def test_bypass_returns_admin_roles(self, app):
        """Bypass user has all roles."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/protected")
        data = response.json()
        assert data["user"]["roles"] == ["admin", "sre", "developer", "security", "viewer"]

    def test_bypass_user_email(self, app):
        """Bypass user has test email."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/protected")
        data = response.json()
        assert data["user"]["email"] == "test@omniwatch.dev"

    def test_bypass_jti(self, app):
        """Bypass user has test session JTI."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/protected")
        data = response.json()
        assert data["user"]["jti"] == "test-session"

    def test_audit_log_not_called(self, app):
        """Bypass mode skips audit logging."""
        with patch("auth.middleware._audit_logger") as mock_audit:
            importlib.reload(auth.middleware)
            from auth.middleware import require_auth as fresh_require_auth

            test_app = FastAPI()

            @test_app.get("/protected2")
            async def protected2(user=Depends(fresh_require_auth("incidents", "read"))):
                return {"user": user}

            client = TestClient(test_app, raise_server_exceptions=False)
            client.get("/protected2")
            mock_audit.log_event.assert_not_called()
