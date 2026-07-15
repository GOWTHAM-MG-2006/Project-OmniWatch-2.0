"""OmniWatch 2.0 — NexusUX: Config Drift Route"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Optional, List
from datetime import datetime

from auth.middleware import require_auth
from compliance.audit_logger import AuditLogger
from dashboard.backend.services.data_service import DataService

router = APIRouter()
audit_logger = AuditLogger()
data_service = DataService()


# ─── Pydantic Models ───────────────────────────────────────────────

class ConfigDriftResponse(BaseModel):
    drift_id: str
    drift_source: str
    drifted_entity: str
    expected_state: Optional[str] = None
    actual_state: Optional[str] = None
    status: str
    confidence: Optional[float] = None
    created_at: Optional[datetime] = None


class ConfigDriftListResponse(BaseModel):
    drifts: List[ConfigDriftResponse]
    total: int


class DriftRemediationResponse(BaseModel):
    drift_id: str
    remediation_status: str


class DriftSourcesResponse(BaseModel):
    sources: List[str]


# ─── Endpoints (static routes BEFORE parameterized routes) ─────────

@router.get("/", response_model=ConfigDriftListResponse)
async def list_config_drifts(
    source: Optional[str] = None,
    status: Optional[str] = None,
    user: dict = Depends(require_auth("config_drift", "read")),
):
    """List configuration drifts."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="config_drift",
        resource_id=None,
        action="list",
        outcome="success",
        metadata={"source": source, "status": status},
    )
    drifts = data_service.get_config_drifts()
    return {"drifts": drifts, "total": len(drifts)}


@router.get("/sources", response_model=DriftSourcesResponse)
async def list_drift_sources(
    user: dict = Depends(require_auth("config_drift", "read")),
):
    """List available drift sources."""
    valid_sources = ["kubernetes", "terraform", "ansible", "git"]
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="config_drift",
        resource_id=None,
        action="sources",
        outcome="success",
    )
    return {"sources": valid_sources}


@router.post("/{drift_id}/remediate", response_model=DriftRemediationResponse)
async def remediate_drift(
    drift_id: str,
    data: Optional[dict] = None,
    user: dict = Depends(require_auth("config_drift", "write")),
):
    """Trigger remediation for a drift."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="config_drift",
        resource_id=drift_id,
        action="remediate",
        outcome="success",
    )
    return {"drift_id": drift_id, "remediation_status": "started"}


@router.get("/{drift_id}", response_model=ConfigDriftResponse)
async def get_config_drift(
    drift_id: str,
    user: dict = Depends(require_auth("config_drift", "read")),
):
    """Get a specific config drift."""
    drift = None
    if not drift:
        raise HTTPException(status_code=404, detail=f"Config drift {drift_id} not found")
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="config_drift",
        resource_id=drift_id,
        action="get",
        outcome="success",
    )
    return drift
