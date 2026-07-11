"""OmniWatch 2.0 — NexusUX: Security Route"""

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

class SecurityEventResponse(BaseModel):
    event_id: str
    attack_type: Optional[str] = None
    entity_id: Optional[str] = None
    severity: str
    confidence: Optional[float] = None
    timestamp: Optional[datetime] = None


class SecurityEventListResponse(BaseModel):
    events: List[SecurityEventResponse]
    total: int


class VulnerabilityResponse(BaseModel):
    vulnerability_id: str
    cve_id: Optional[str] = None
    entity_id: Optional[str] = None
    severity: str
    description: Optional[str] = None


class VulnerabilityListResponse(BaseModel):
    vulnerabilities: List[VulnerabilityResponse]
    total: int


class CSPMStatusResponse(BaseModel):
    compliant: int
    non_compliant: int
    total_checks: int


class AttackMapResponse(BaseModel):
    tactics: List[Any]
    techniques: List[Any]


# ─── Endpoints ─────────────────────────────────────────────────────

@router.get("/events", response_model=SecurityEventListResponse)
async def list_security_events(
    severity: Optional[str] = None,
    user: dict = Depends(require_auth("security_events", "read")),
):
    """List security events."""
    valid_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    if severity and severity.upper() not in valid_severities:
        raise HTTPException(status_code=400, detail=f"Invalid severity '{severity}'. Valid values: {valid_severities}")
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="security_event",
        resource_id=None,
        action="list",
        outcome="success",
        metadata={"severity": severity},
    )
    events = data_service.get_security_events(severity)
    return {"events": events, "total": len(events)}


@router.get("/vulnerabilities", response_model=VulnerabilityListResponse)
async def list_vulnerabilities(
    user: dict = Depends(require_auth("vulnerabilities", "read")),
):
    """List known vulnerabilities."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="vulnerability",
        resource_id=None,
        action="list",
        outcome="success",
    )
    vulns = data_service.get_vulnerabilities()
    return {"vulnerabilities": vulns, "total": len(vulns)}


@router.get("/cspm", response_model=CSPMStatusResponse)
async def get_cspm_status(
    user: dict = Depends(require_auth("cspm", "read")),
):
    """Get Cloud Security Posture Management status."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="cspm",
        resource_id=None,
        action="status",
        outcome="success",
    )
    return {"compliant": 0, "non_compliant": 0, "total_checks": 0}


@router.get("/attack-map", response_model=AttackMapResponse)
async def get_attack_map(
    user: dict = Depends(require_auth("security_events", "read")),
):
    """Get MITRE ATT&CK map of detected threats."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="security_event",
        resource_id=None,
        action="attack_map",
        outcome="success",
    )
    return {"tactics": [], "techniques": []}
