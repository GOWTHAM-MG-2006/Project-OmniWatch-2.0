"""OmniWatch 2.0 — NexusUX: Simulations Route"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Optional, List
from datetime import datetime

from auth.middleware import require_auth
from compliance.audit_logger import AuditLogger
from dashboard.backend.services.data_service import DataService
from dashboard.backend.services.simulax_service import SimulaXService

router = APIRouter()
audit_logger = AuditLogger()
data_service = DataService()
sim_service = SimulaXService()


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
    simulations = data_service.get_simulations()
    return {"simulations": simulations, "total": len(simulations)}


@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(
    simulation_id: str,
    user: dict = Depends(require_auth("simulations", "read")),
):
    """Get a specific simulation result."""
    # TODO: Replace with real database lookup
    simulation = None  # db.get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="simulation",
        resource_id=simulation_id,
        action="get",
        outcome="success",
    )
    return simulation


@router.post("/", response_model=SimulationResponse, status_code=202)
async def run_simulation(
    data: SimulationRunRequest,
    user: dict = Depends(require_auth("simulations", "write")),
):
    """Run a new simulation."""
    if data.mode == "REMEDIATION_SIMULATION":
        result = sim_service.run_remediation_sim(data.parameters or {})
    elif data.mode == "CAPACITY_SIMULATION":
        result = sim_service.run_capacity_sim(data.parameters or {})
    elif data.mode == "DEPLOYMENT_SIMULATION":
        result = sim_service.run_deployment_sim(data.parameters or {})
    elif data.mode == "CHAOS_SIMULATION":
        result = sim_service.run_chaos_sim(data.parameters or {})
    else:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {data.mode}")
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="simulation",
        resource_id=None,
        action="run",
        outcome="success",
        metadata={"mode": data.mode},
    )
    return result


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
