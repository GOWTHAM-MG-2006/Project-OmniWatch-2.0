"""OmniWatch 2.0 — NexusUX: Incidents Route"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Optional, List

from auth.middleware import require_auth
from compliance.audit_logger import AuditLogger
from dashboard.backend.services.data_service import DataService

router = APIRouter()
audit_logger = AuditLogger()
data_service = DataService()


class IncidentResponse(BaseModel):
    incident_id: str
    created_at: Optional[datetime] = None
    severity: str
    business_impact_score: Optional[float] = None
    root_cause: Optional[str] = None
    status: str
    assigned_to: Optional[str] = None


class IncidentListResponse(BaseModel):
    incidents: List[IncidentResponse]
    total: int


class IncidentCreateRequest(BaseModel):
    severity: str
    title: str
    description: Optional[str] = None


class IncidentUpdateRequest(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None


@router.get("/", response_model=IncidentListResponse)
async def list_incidents(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    user: dict = Depends(require_auth("incidents", "read")),
):
    """List all incidents."""
    incidents = data_service.get_active_incidents(status=status or "OPEN")
    return {"incidents": incidents, "total": len(incidents)}


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    user: dict = Depends(require_auth("incidents", "read")),
):
    """Get a specific incident."""
    incident = data_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident


@router.post("/", response_model=IncidentResponse, status_code=201)
async def create_incident(
    data: IncidentCreateRequest,
    user: dict = Depends(require_auth("incidents", "write")),
):
    """Create a new incident."""
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    user_id = user.get("user_id", "unknown")

    insert_query = """
    INSERT INTO incidents (incident_id, severity, root_cause, status, assigned_to, created_at)
    VALUES ({id:String}, {severity:String}, {title:String}, 'OPEN', {user:String}, now())
    """
    data_service._execute(insert_query, {
        "id": incident_id,
        "severity": data.severity,
        "title": data.title or data.description or "",
        "user": user_id,
    })

    audit_logger.log_event(
        event_type="api_call",
        user_id=user_id,
        resource_type="incident",
        action="create",
        outcome="success",
        resource_id=incident_id,
    )

    return {
        "incident_id": incident_id,
        "severity": data.severity,
        "status": "OPEN",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    data: IncidentUpdateRequest,
    user: dict = Depends(require_auth("incidents", "write")),
):
    """Update an incident."""
    incident = data_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    updates = []
    params = {"id": incident_id}
    if data.status:
        updates.append("status = {status:String}")
        params["status"] = data.status
    if data.assigned_to:
        updates.append("assigned_to = {assigned:String}")
        params["assigned"] = data.assigned_to

    if updates:
        update_query = f"ALTER TABLE incidents UPDATE {', '.join(updates)} WHERE incident_id = {{id:String}}"
        data_service._execute(update_query, params)

    return {
        "incident_id": incident_id,
        "severity": incident.get("severity", "P3"),
        "status": data.status or incident.get("status", "OPEN"),
        "assigned_to": data.assigned_to or incident.get("assigned_to"),
    }


@router.get("/{incident_id}/timeline")
async def get_incident_timeline(
    incident_id: str,
    user: dict = Depends(require_auth("incidents", "read")),
):
    """Get the timeline for an incident."""
    incident = data_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return {"incident_id": incident_id, "timeline": []}
