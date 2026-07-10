"""
OmniWatch 2.0 — Auth (Middleware)
Component: FastAPI Auth Middleware
Layer: Enterprise
Phase: 6
Purpose: JWT authentication + RBAC authorization enforcement via FastAPI Depends
Inputs: Authorization header (Bearer JWT), endpoint resource/action
Outputs: Authenticated user dict on success, 401/403 on failure, audit log entry
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request

from auth.sso_provider import SSOProvider
from auth.rbac_manager import RBACManager

logger = logging.getLogger(__name__)

# Module-level singletons — lazy-initialized, overridable in tests
_sso_provider: Optional[SSOProvider] = None
_rbac_manager: Optional[RBACManager] = None
_audit_logger = None


def _get_sso_provider() -> SSOProvider:
    global _sso_provider
    if _sso_provider is None:
        _sso_provider = SSOProvider()
    return _sso_provider


def _get_rbac_manager() -> RBACManager:
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager


def _get_audit_logger():
    global _audit_logger
    if _audit_logger is None:
        from compliance.audit_logger import AuditLogger
        _audit_logger = AuditLogger()
    return _audit_logger


def _extract_bearer_token(request: Request) -> Optional[str]:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:]


def require_auth(resource: str, action: str):
    """
    FastAPI Depends function that enforces JWT authentication + RBAC authorization.

    Usage:
        @app.get("/incidents")
        async def list_incidents(user=Depends(require_auth("incidents", "read"))):
            ...

    Args:
        resource: The resource type being accessed (e.g., "incidents", "topology").
        action: The action being performed (e.g., "read", "write", "execute").

    Returns:
        A FastAPI dependency that returns the authenticated user dict on success,
        raises HTTPException(401) for auth failures or HTTPException(403) for
        insufficient permissions.
    """

    async def _auth_dependency(request: Request) -> dict:
        sso = _get_sso_provider()
        rbac = _get_rbac_manager()
        audit = _get_audit_logger()

        # Step 1: Extract token from header
        token = _extract_bearer_token(request)
        if not token:
            logger.warning("Missing or malformed Authorization header")
            _log_access_decision(
                audit, request, user_id="anonymous",
                resource=resource, action=action, outcome="denied",
                detail="Missing authentication token",
            )
            raise HTTPException(status_code=401, detail="Authentication required")

        # Step 2: Validate JWT
        payload = sso.validate_token(token)
        if payload is None:
            logger.warning("Invalid or expired JWT token")
            _log_access_decision(
                audit, request, user_id="anonymous",
                resource=resource, action=action, outcome="denied",
                detail="Invalid or expired token",
            )
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_id = payload.get("user_id", "unknown")
        email = payload.get("email", "")
        roles = payload.get("roles", [])

        # Step 3: RBAC permission check
        # Check if any of the user's roles grant the required permission
        authorized = False
        for role in roles:
            if rbac.has_permission(role, resource, action):
                authorized = True
                break

        if not authorized:
            logger.warning(
                "User %s denied %s:%s (roles=%s)",
                user_id, resource, action, roles
            )
            _log_access_decision(
                audit, request, user_id=user_id,
                resource=resource, action=action, outcome="denied",
                detail="Roles %s lack %s:%s permission" % (roles, resource, action),
            )
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Step 4: Success — log and return user context
        logger.debug("User %s authorized for %s:%s", user_id, resource, action)
        _log_access_decision(
            audit, request, user_id=user_id,
            resource=resource, action=action, outcome="success",
        )

        return {
            "user_id": user_id,
            "email": email,
            "roles": roles,
            "jti": payload.get("jti"),
        }

    return _auth_dependency


def _log_access_decision(
    audit_logger,
    request: Request,
    user_id: str,
    resource: str,
    action: str,
    outcome: str,
    detail: str = "",
):
    """Log access decision to the audit trail (best-effort, never blocks)."""
    try:
        client_ip = request.client.host if request.client else "unknown"
        metadata = {"detail": detail} if detail else None
        audit_logger.log_event(
            event_type="api_call",
            user_id=user_id,
            resource_type="endpoint",
            resource_id="%s %s" % (request.method, request.url.path),
            action=action,
            outcome=outcome,
            ip_address=client_ip,
            metadata=metadata,
        )
    except Exception as exc:
        logger.error("Failed to write audit log: %s", str(exc))
