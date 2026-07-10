"""
OmniWatch 2.0 — Auth (RBAC Manager)
Component: RBACManager
Layer: Enterprise
Phase: 6
Purpose: Role-Based Access Control with 5 predefined roles
Inputs: Role assignments from Redis
Outputs: Permission checks (bool) for resource+action pairs
"""

import os
import logging
from typing import Optional

import redis

logger = logging.getLogger(__name__)

ROLE_PERMISSIONS = {
    "admin": {
        "*": ["*"],
    },
    "sre": {
        "incidents": ["read", "write", "delete"],
        "topology": ["read"],
        "remediation": ["execute"],
        "policies": ["read", "write"],
        "metrics": ["read"],
        "logs": ["read"],
    },
    "developer": {
        "services": ["read"],
        "traces": ["read"],
        "metrics": ["read"],
        "incidents": ["read"],
        "logs": ["read"],
    },
    "viewer": {
        "dashboard": ["read"],
        "incidents": ["read"],
        "topology": ["read"],
        "services": ["read"],
    },
    "security": {
        "security_events": ["read"],
        "vulnerabilities": ["read"],
        "cspm": ["read"],
        "incidents": ["read"],
    },
}


class RBACManager:
    """
    Role-Based Access Control manager with Redis-backed role storage.
    Provides permission checks for the 5 predefined roles:
    admin, sre, developer, viewer, security.
    """

    REDIS_KEY = "user_roles"

    def __init__(
        self,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_db: int = 0,
    ):
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

    def has_permission(self, role: str, resource: str, action: str) -> bool:
        """
        Check if a role has permission for a given resource and action.

        Args:
            role: The role name (admin, sre, developer, viewer, security).
            resource: The resource type (incidents, topology, remediation, etc.).
            action: The action (read, write, delete, execute).

        Returns:
            True if the role has permission, False otherwise.
        """
        if role not in ROLE_PERMISSIONS:
            logger.debug(f"Unknown role '{role}' denied access to {resource}:{action}")
            return False

        role_perms = ROLE_PERMISSIONS[role]

        # Admin wildcard: has access to everything
        if "*" in role_perms and "*" in role_perms["*"]:
            return True

        # Check if resource exists in role permissions
        if resource not in role_perms:
            return False

        # Check if action is allowed for this resource
        allowed_actions = role_perms[resource]
        return action in allowed_actions

    def assign_role(self, user_id: str, role: str) -> None:
        """
        Assign a role to a user. Stored in Redis hash.

        Args:
            user_id: The user identifier.
            role: The role to assign (must be one of the 5 predefined roles).
        """
        self.redis_client.hset(self.REDIS_KEY, user_id, role)
        logger.info("Assigned role '%s' to user '%s'", role, user_id)

    def get_user_role(self, user_id: str) -> Optional[str]:
        """
        Retrieve the role assigned to a user.

        Args:
            user_id: The user identifier.

        Returns:
            The role name if found, None otherwise.
        """
        role = self.redis_client.hget(self.REDIS_KEY, user_id)
        return role
