"""OmniWatch 2.0 — NexusUX: Simulations Route"""

from fastapi import APIRouter
from typing import Any

router = APIRouter()


@router.get("/")
async def list_simulations(mode: str | None = None):
    """List all simulations."""
    return {"simulations": [], "total": 0}


@router.get("/{simulation_id}")
async def get_simulation(simulation_id: str):
    """Get a specific simulation result."""
    return {"simulation_id": simulation_id, "status": "not_found"}


@router.post("/")
async def run_simulation(data: dict[str, Any]):
    """Run a new simulation."""
    return {"simulation_id": "SIM-NEW", "status": "started"}


@router.get("/modes")
async def list_simulation_modes():
    """List available simulation modes."""
    return {"modes": ["REMEDIATION_SIMULATION", "CAPACITY_SIMULATION", "DEPLOYMENT_SIMULATION", "CHAOS_SIMULATION"]}
