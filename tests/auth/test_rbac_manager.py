"""
OmniWatch 2.0 — Auth (RBAC Manager)
Component: RBACManager Tests
Layer: Enterprise
Phase: 6
Purpose: Tests for Role-Based Access Control manager
Inputs: Mock Redis, predefined roles
Outputs: Test assertions for permission checks
"""

import pytest
from unittest.mock import MagicMock

from auth.rbac_manager import RBACManager


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = MagicMock()
    mock.hset.return_value = True
    mock.hget.return_value = None
    mock.hgetall.return_value = {}
    mock.ping.return_value = True
    return mock


@pytest.fixture
def rbac_manager(mock_redis):
    """RBACManager with mocked Redis."""
    manager = RBACManager(redis_host="localhost", redis_port=6379)
    manager._redis_client = mock_redis
    return manager


class TestRolePermissions:
    """Tests for role-based permission checks."""

    def test_admin_has_full_access(self, rbac_manager):
        """Admin can do anything on any resource."""
        # Admin should have access to all resources
        assert rbac_manager.has_permission("admin", "incidents", "read") is True
        assert rbac_manager.has_permission("admin", "incidents", "write") is True
        assert rbac_manager.has_permission("admin", "incidents", "delete") is True
        assert rbac_manager.has_permission("admin", "topology", "read") is True
        assert rbac_manager.has_permission("admin", "remediation", "execute") is True
        assert rbac_manager.has_permission("admin", "policies", "read") is True
        assert rbac_manager.has_permission("admin", "services", "read") is True
        assert rbac_manager.has_permission("admin", "traces", "read") is True
        assert rbac_manager.has_permission("admin", "security_events", "read") is True
        assert rbac_manager.has_permission("admin", "vulnerabilities", "read") is True

    def test_viewer_cannot_write(self, rbac_manager):
        """Viewer can read but not delete/execute."""
        # Viewer should have read access to dashboard
        assert rbac_manager.has_permission("viewer", "dashboard", "read") is True
        # Viewer should NOT have write/delete/execute access
        assert rbac_manager.has_permission("viewer", "incidents", "write") is False
        assert rbac_manager.has_permission("viewer", "incidents", "delete") is False
        assert rbac_manager.has_permission("viewer", "remediation", "execute") is False
        assert rbac_manager.has_permission("viewer", "topology", "write") is False

    def test_sre_can_execute_remediation(self, rbac_manager):
        """SRE has remediation execute permission."""
        # SRE should have access to incidents (CRUD)
        assert rbac_manager.has_permission("sre", "incidents", "read") is True
        assert rbac_manager.has_permission("sre", "incidents", "write") is True
        assert rbac_manager.has_permission("sre", "incidents", "delete") is True
        # SRE should have remediation execute
        assert rbac_manager.has_permission("sre", "remediation", "execute") is True
        # SRE should have topology read
        assert rbac_manager.has_permission("sre", "topology", "read") is True
        # SRE should have policies read/write
        assert rbac_manager.has_permission("sre", "policies", "read") is True
        assert rbac_manager.has_permission("sre", "policies", "write") is True

    def test_developer_limited_access(self, rbac_manager):
        """Developer can read services/traces but not remediate."""
        # Developer should have read access to services
        assert rbac_manager.has_permission("developer", "services", "read") is True
        # Developer should have read access to traces
        assert rbac_manager.has_permission("developer", "traces", "read") is True
        # Developer should have read access to metrics
        assert rbac_manager.has_permission("developer", "metrics", "read") is True
        # Developer should have read access to incidents
        assert rbac_manager.has_permission("developer", "incidents", "read") is True
        # Developer should NOT have remediation execute
        assert rbac_manager.has_permission("developer", "remediation", "execute") is False
        # Developer should NOT have write/delete access
        assert rbac_manager.has_permission("developer", "services", "write") is False
        assert rbac_manager.has_permission("developer", "incidents", "delete") is False

    def test_security_role_access(self, rbac_manager):
        """Security can read security_events/vulnerabilities."""
        # Security should have read access to security_events
        assert rbac_manager.has_permission("security", "security_events", "read") is True
        # Security should have read access to vulnerabilities
        assert rbac_manager.has_permission("security", "vulnerabilities", "read") is True
        # Security should NOT have remediation execute
        assert rbac_manager.has_permission("security", "remediation", "execute") is False
        # Security should NOT have write access to incidents
        assert rbac_manager.has_permission("security", "incidents", "write") is False

    def test_unknown_role_denied(self, rbac_manager):
        """Unknown role gets denied for everything."""
        # Unknown role should be denied for all resources
        assert rbac_manager.has_permission("unknown_role", "incidents", "read") is False
        assert rbac_manager.has_permission("unknown_role", "dashboard", "read") is False
        assert rbac_manager.has_permission("unknown_role", "remediation", "execute") is False
        assert rbac_manager.has_permission("hacker", "security_events", "read") is False


class TestRoleAssignment:
    """Tests for role assignment and retrieval via Redis."""

    def test_assign_role_stores_in_redis(self, rbac_manager, mock_redis):
        """Role assignment should store role in Redis."""
        rbac_manager.assign_role("user-123", "sre")
        
        mock_redis.hset.assert_called_once_with("user_roles", "user-123", "sre")

    def test_get_user_role_retrieves_from_redis(self, rbac_manager, mock_redis):
        """Role retrieval should fetch role from Redis."""
        mock_redis.hget.return_value = "admin"
        
        role = rbac_manager.get_user_role("user-456")
        
        assert role == "admin"
        mock_redis.hget.assert_called_once_with("user_roles", "user-456")

    def test_get_user_role_returns_none_when_not_found(self, rbac_manager, mock_redis):
        """Role retrieval returns None when user has no role."""
        mock_redis.hget.return_value = None
        
        role = rbac_manager.get_user_role("user-unknown")
        
        assert role is None
