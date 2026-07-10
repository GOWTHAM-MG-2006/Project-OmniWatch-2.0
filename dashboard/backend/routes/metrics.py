"""OmniWatch 2.0 — NexusUX: Metrics Route"""

from fastapi import APIRouter
from typing import Any

router = APIRouter()


@router.get("/")
async def list_metrics(entity_id: str | None = None, metric_name: str | None = None):
    """List metrics with optional filters."""
    return {"metrics": [], "total": 0}


@router.get("/entity/{entity_id}")
async def get_entity_metrics(entity_id: str):
    """Get metrics for a specific entity."""
    return {"entity_id": entity_id, "metrics": []}


@router.get("/summary")
async def get_metrics_summary():
    """Get overall metrics summary."""
    return {
        "total_entities": 0,
        "healthy": 0,
        "degraded": 0,
        "unhealthy": 0,
        "active_anomalies": 0,
    }


@router.get("/cost-carbon")
async def get_cost_carbon(entity_id: str | None = None):
    """Get cost and carbon metrics."""
    return {"entities": [], "total_hourly_cost_usd": 0, "total_carbon_grams": 0}
