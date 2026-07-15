"""OmniWatch 2.0 — NexusUX: Policies Route"""

import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from config import config
from auth.middleware import require_auth
from compliance.audit_logger import AuditLogger

logger = logging.getLogger(__name__)
router = APIRouter()
audit_logger = AuditLogger()

OPA_ENDPOINT = config.OPA_URL


class PolicyResponse(BaseModel):
    name: str
    package: str
    status: str
    content: Optional[str] = None


class PolicyListResponse(BaseModel):
    policies: list[dict]
    total: int


class PolicyUpdateRequest(BaseModel):
    content: str


@router.get("/", response_model=PolicyListResponse)
async def list_policies(
    user: dict = Depends(require_auth("policies", "read")),
):
    """List all OPA policies from the OPA server."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=config.OPA_HTTP_TIMEOUT) as client:
            response = await client.get(f"{OPA_ENDPOINT}/v1/policies")
            response.raise_for_status()
            data = response.json()

        policies = []
        result = data.get("result", {})
        if isinstance(result, dict):
            for path, policy_data in result.items():
                policy_name = path.lstrip("/").replace("/", ".")
                policies.append({
                    "name": policy_name,
                    "package": policy_data.get("package", ""),
                    "status": "active",
                })
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    path = item.get("path", "")
                    policy_name = path.lstrip("/").replace("/", ".")
                    policies.append({
                        "name": policy_name,
                        "package": item.get("package", ""),
                        "status": "active",
                    })

        audit_logger.log_event(
            event_type="api_call",
            user_id=user.get("user_id"),
            resource_type="policy",
            action="list",
            outcome="success",
            resource_id=None,
        )

        return {"policies": policies, "total": len(policies)}
    except Exception as e:
        logger.warning("OPA not available: %s", e)
        return {"policies": [], "total": 0}


@router.get("/{policy_name}")
async def get_policy(
    policy_name: str,
    user: dict = Depends(require_auth("policies", "read")),
):
    """Get a specific OPA policy's Rego content."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=config.OPA_HTTP_TIMEOUT) as client:
            response = await client.get(f"{OPA_ENDPOINT}/v1/policies/{policy_name}")
            response.raise_for_status()
            data = response.json()

        result = data.get("result", {})
        audit_logger.log_event(
            event_type="api_call",
            user_id=user.get("user_id"),
            resource_type="policy",
            action="get",
            outcome="success",
            resource_id=policy_name,
        )

        return {
            "name": policy_name,
            "package": result.get("package", ""),
            "content": result.get("raw", ""),
            "rego": result.get("rego", ""),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Policy {policy_name} not found")
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"OPA unavailable: {str(e)}")


@router.put("/{policy_name}")
async def update_policy(
    policy_name: str,
    data: PolicyUpdateRequest,
    user: dict = Depends(require_auth("policies", "write")),
):
    """Update an OPA policy's Rego content."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=config.OPA_HTTP_TIMEOUT) as client:
            response = await client.put(
                f"{OPA_ENDPOINT}/v1/policies/{policy_name}",
                data=data.content,
                headers={"Content-Type": "text/plain"},
            )
            response.raise_for_status()

        audit_logger.log_event(
            event_type="api_call",
            user_id=user.get("user_id"),
            resource_type="policy",
            action="update",
            outcome="success",
            resource_id=policy_name,
        )

        return {"name": policy_name, "status": "updated"}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Failed to update policy: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"OPA unavailable: {str(e)}")
