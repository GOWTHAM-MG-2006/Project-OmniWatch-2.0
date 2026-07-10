"""
OmniWatch 2.0 — Auth (Middleware)
Component: Auth Middleware Tests
Layer: Enterprise
Phase: 6
Purpose: Tests for FastAPI auth middleware with JWT + RBAC enforcement
Inputs: Mock SSOProvider, mock RBACManager
Outputs: Test assertions for 401/403 responses
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

# Set test environment before importing auth modules
os.environ["TESTING"] = "1"

from auth.middleware import require_auth


@pytest.fixture
def mock_sso_provider():
    """Mock SSOProvider."""
    mock = MagicMock()
    mock.validate_token.return_value = None
    return mock


@pytest.fixture
def mock_rbac_manager():
    """Mock RBACManager."""
    mock = MagicMock()
    mock.has_permission.return_value = False
    mock.get_user_role.return_value = None
    return mock


@pytest.fixture
def mock_audit_logger():
    """Mock AuditLogger."""
    mock = MagicMock()
    mock.log_event.return_value = "event-id-123"
    return mock


@pytest.fixture
def app(mock_sso_provider, mock_rbac_manager, mock_audit_logger):
    """FastAPI test app with auth-protected endpoint."""
    test_app = FastAPI()

    @test_app.get("/protected")
    async def protected_endpoint(
        user=Depends(require_auth("incidents", "read")),
    ):
        return {"message": "success", "user": user}

    # Patch the module-level singletons used by require_auth
    with patch("auth.middleware._sso_provider", mock_sso_provider), \
         patch("auth.middleware._rbac_manager", mock_rbac_manager), \
         patch("auth.middleware._audit_logger", mock_audit_logger):
        yield test_app, mock_sso_provider, mock_rbac_manager, mock_audit_logger


class TestUnauthenticatedReturns401:
    """Tests for missing/invalid token returning 401."""

    def test_no_token_returns_401(self, app):
        """No Authorization header → 401."""
        test_app, mock_sso, mock_rbac, mock_audit = app
        client = TestClient(test_app, raise_server_exceptions=False)

        response = client.get("/protected")

        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication required"

    def test_malformed_token_returns_401(self, app):
        """Invalid token format → 401."""
        test_app, mock_sso, mock_rbac, mock_audit = app
        mock_sso.validate_token.return_value = None
        client = TestClient(test_app, raise_server_exceptions=False)

        response = client.get("/protected", headers={"Authorization": "Bearer invalid.token.here"})

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired token"

    def test_expired_token_returns_401(self, app):
        """Expired JWT → 401."""
        test_app, mock_sso, mock_rbac, mock_audit = app
        mock_sso.validate_token.return_value = None
        client = TestClient(test_app, raise_server_exceptions=False)

        response = client.get("/protected", headers={"Authorization": "Bearer expired.jwt.token"})

        assert response.status_code == 401

    def test_malformed_auth_header_returns_401(self, app):
        """Missing 'Bearer' prefix → 401."""
        test_app, mock_sso, mock_rbac, mock_audit = app
        client = TestClient(test_app, raise_server_exceptions=False)

        response = client.get("/protected", headers={"Authorization": "Token some-token"})

        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication required"

    def test_valid_jwt_unknown_role_returns_403(self, app):
        """Valid JWT with a role not defined in RBAC → 403."""
        test_app, mock_sso, mock_rbac, mock_audit = app
        mock_sso.validate_token.return_value = {
            "user_id": "user-ghost",
            "email": "ghost@example.com",
            "roles": ["nonexistent_role"],
            "type": "access",
        }
        mock_rbac.has_permission.return_value = False
        client = TestClient(test_app, raise_server_exceptions=False)

        response = client.get("/protected", headers={"Authorization": "Bearer some.jwt.token"})

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions"


class TestUnauthorizedReturns403:
    """Tests for valid token but insufficient permissions returning 403."""

    def test_valid_token_insufficient_permissions_returns_403(self, app):
        """Valid JWT but role lacks required permission → 403."""
        test_app, mock_sso, mock_rbac, mock_audit = app
        mock_sso.validate_token.return_value = {
            "user_id": "user-viewer",
            "email": "viewer@example.com",
            "roles": ["viewer"],
            "type": "access",
        }
        # RBAC denies the permission
        mock_rbac.has_permission.return_value = False
        client = TestClient(test_app, raise_server_exceptions=False)

        response = client.get("/protected", headers={"Authorization": "Bearer valid.jwt.token"})

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions"

    def test_viewer_cannot_write_incidents(self, app):
        """Viewer role with write action → 403."""
        test_app, mock_sso, mock_rbac, mock_audit = app
        mock_sso.validate_token.return_value = {
            "user_id": "user-viewer",
            "email": "viewer@example.com",
            "roles": ["viewer"],
            "type": "access",
        }
        mock_rbac.has_permission.return_value = False
        client = TestClient(test_app, raise_server_exceptions=False)

        response = client.get("/protected", headers={"Authorization": "Bearer valid.jwt.token"})

        assert response.status_code == 403

    def test_authenticated_and_authorized_returns_200(self, app):
        """Valid JWT with correct permissions → 200."""
        test_app, mock_sso, mock_rbac, mock_audit = app
        mock_sso.validate_token.return_value = {
            "user_id": "user-admin",
            "email": "admin@example.com",
            "roles": ["admin"],
            "type": "access",
        }
        mock_rbac.has_permission.return_value = True
        client = TestClient(test_app, raise_server_exceptions=False)

        response = client.get("/protected", headers={"Authorization": "Bearer valid.jwt.token"})

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "success"
        assert data["user"]["user_id"] == "user-admin"

    def test_audit_log_recorded_on_success(self, app):
        """Successful request should log audit event."""
        test_app, mock_sso, mock_rbac, mock_audit = app
        mock_sso.validate_token.return_value = {
            "user_id": "user-sre",
            "email": "sre@example.com",
            "roles": ["sre"],
            "type": "access",
        }
        mock_rbac.has_permission.return_value = True
        client = TestClient(test_app, raise_server_exceptions=False)

        client.get("/protected", headers={"Authorization": "Bearer valid.jwt.token"})

        mock_audit.log_event.assert_called_once()
        call_kwargs = mock_audit.log_event.call_args[1]
        assert call_kwargs["event_type"] == "api_call"
        assert call_kwargs["user_id"] == "user-sre"
        assert call_kwargs["outcome"] == "success"

    def test_audit_log_recorded_on_denial(self, app):
        """Denied request should log audit event."""
        test_app, mock_sso, mock_rbac, mock_audit = app
        mock_sso.validate_token.return_value = {
            "user_id": "user-viewer",
            "email": "viewer@example.com",
            "roles": ["viewer"],
            "type": "access",
        }
        mock_rbac.has_permission.return_value = False
        client = TestClient(test_app, raise_server_exceptions=False)

        client.get("/protected", headers={"Authorization": "Bearer valid.jwt.token"})

        mock_audit.log_event.assert_called_once()
        call_kwargs = mock_audit.log_event.call_args[1]
        assert call_kwargs["event_type"] == "api_call"
        assert call_kwargs["user_id"] == "user-viewer"
        assert call_kwargs["outcome"] == "denied"
