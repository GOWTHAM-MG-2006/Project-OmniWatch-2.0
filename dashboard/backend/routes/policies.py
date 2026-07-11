"""OmniWatch 2.0 — NexusUX: Policies Route"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Optional, List

from auth.middleware import require_auth
from compliance.audit_logger import AuditLogger

router = APIRouter()
audit_logger = AuditLogger()


class PolicyResponse(BaseModel):
    name: str
    package: str
    status: str
    content: Optional[str] = None


class PolicyListResponse(BaseModel):
    policies: List[PolicyResponse]
    total: int


@router.get("/", response_model=PolicyListResponse)
async def list_policies(
    user: dict = Depends(require_auth("policies", "read")),
):
    """List OPA policies."""
    return {
        "policies": [
            {"name": "remediation", "package": "omniwatch.remediation", "status": "active"},
            {"name": "security", "package": "omniwatch.security", "status": "active"},
            {"name": "config_drift", "package": "omniwatch.config_drift", "status": "active"},
        ],
        "total": 3,
    }


@router.get("/{policy_name}")
async def get_policy(
    policy_name: str,
    user: dict = Depends(require_auth("policies", "read")),
):
    """Get a specific policy."""
    policies = {
        "remediation": {"name": "remediation", "package": "omniwatch.remediation", "status": "active", "content": "package omniwatch.remediation\n\ndef allow {\n  input.action == \"auto\"\n}"},
        "security": {"name": "security", "package": "omniwatch.security", "status": "active", "content": "package omniwatch.security\n\ndef allow {\n  input.severity != \"CRITICAL\"\n}"},
        "config_drift": {"name": "config_drift", "package": "omniwatch.config_drift", "status": "active", "content": "package omniwatch.config_drift\n\ndef allow {\n  input.source == \"kubernetes\"\n}"},
    }
    if policy_name not in policies:
        raise HTTPException(status_code=404, detail=f"Policy {policy_name} not found")
    return policies[policy_name]


@router.put("/{policy_name}")
async def update_policy(
    policy_name: str,
    data: dict,
    user: dict = Depends(require_auth("policies", "write")),
):
    """Update a policy."""
    if policy_name not in ["remediation", "security", "config_drift"]:
        raise HTTPException(status_code=404, detail=f"Policy {policy_name} not found")
    return {"name": policy_name, "status": "updated", "content": data.get("content", "")}
