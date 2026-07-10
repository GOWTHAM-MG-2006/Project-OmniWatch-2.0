"""OmniWatch 2.0 — NexusUX: Simulations Route"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Optional, List
from datetime import datetime

from auth.middleware import require_auth
from compliance.audit_logger import AuditLogger

router = APIRouter()
audit_logger = AuditLogger()


# ─── Pydantic Models ───────────────────────────────────────────────

class SimulationResponse(BaseModel):
    simulation_id: str
    mode: Optional[str] = None
    status: str
    resolution_confidence: Optional[float] = None
    risk_score: Optional[float] = None
    recommendation: Optional[str] = None
    created_at: Optional[datetime] = None


class SimulationListResponse(BaseModel):
    simulations: List[SimulationResponse]
    total: int


class SimulationRunRequest(BaseModel):
    mode: str
    incident_id: Optional[str] = None
    parameters: Optional[dict] = None


class SimulationModesResponse(BaseModel):
    modes: List[str]


# ─── Endpoints ─────────────────────────────────────────────────────

@router.get("/", response_model=SimulationListResponse)
async def list_simulations(
    mode: Optional[str] = None,
    user: dict = Depends(require_auth("simulations", "read")),
):
    """List all simulations."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="simulation",
        resource_id=None,
        action="list",
        outcome="success",
        metadata={"mode": mode},
    )
    return {"simulations": [], "total": 0}


@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(
    simulation_id: str,
    user: dict = Depends(require_auth("simulations", "read")),
):
    """Get a specific simulation result."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="simulation",
        resource_id=simulation_id,
        action="get",
        outcome="success",
    )
    return {"simulation_id": simulation_id, "status": "not_found"}


@router.post("/", response_model=SimulationResponse, status_code=202)
async def run_simulation(
    data: SimulationRunRequest,
    user: dict = Depends(require_auth("simulations", "write")),
):
    """Run a new simulation."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="simulation",
        resource_id=None,
        action="run",
        outcome="success",
        metadata={"mode": data.mode},
    )
    return {"simulation_id": "SIM-NEW", "status": "started"}


@router.get("/modes", response_model=SimulationModesResponse)
async def list_simulation_modes(
    user: dict = Depends(require_auth("simulations", "read")),
):
    """List available simulation modes."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="simulation",
        resource_id=None,
        action="modes",
        outcome="success",
    )
    return {"modes": ["REMEDIATION_SIMULATION", "CAPACITY_SIMULATION", "DEPLOYMENT_SIMULATION", "CHAOS_SIMULATION"]}
