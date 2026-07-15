"""OmniWatch 2.0 — NexusUX: Metrics Route"""

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

class MetricResponse(BaseModel):
    entity_id: str
    metric_name: str
    metric_value: float
    timestamp: Optional[datetime] = None


class MetricListResponse(BaseModel):
    metrics: List[MetricResponse]
    total: int


class MetricsSummaryResponse(BaseModel):
    total_entities: int
    healthy: int
    degraded: int
    unhealthy: int
    active_anomalies: int


class CostCarbonResponse(BaseModel):
    entities: List[Any]
    total_hourly_cost_usd: float
    total_carbon_grams: float


# ─── Endpoints ─────────────────────────────────────────────────────

@router.get("/", response_model=MetricListResponse)
async def list_metrics(
    entity_id: Optional[str] = None,
    metric_name: Optional[str] = None,
    user: dict = Depends(require_auth("metrics", "read")),
):
    """List metrics with optional filters."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="metric",
        resource_id=entity_id,
        action="list",
        outcome="success",
    )
    metrics = data_service.get_live_metrics(entity_id or "all", "1h")
    return {"metrics": metrics, "total": len(metrics)}


@router.get("/entity/{entity_id}", response_model=MetricListResponse)
async def get_entity_metrics(
    entity_id: str,
    user: dict = Depends(require_auth("metrics", "read")),
):
    """Get metrics for a specific entity."""
    metrics = data_service.get_live_metrics(entity_id, "1h")
    return {"metrics": metrics, "total": len(metrics)}


@router.get("/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary(
    user: dict = Depends(require_auth("metrics", "read")),
):
    """Get overall metrics summary."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="metric",
        resource_id=None,
        action="summary",
        outcome="success",
    )
    return data_service.get_metrics_summary()


@router.get("/cost-carbon", response_model=CostCarbonResponse)
async def get_cost_carbon(
    entity_id: Optional[str] = None,
    user: dict = Depends(require_auth("metrics", "read")),
):
    """Get cost and carbon metrics."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="metric",
        resource_id=entity_id,
        action="cost_carbon",
        outcome="success",
    )
    return data_service.get_cost_carbon()


@router.get("/slo")
async def get_slo_compliance(
    user: dict = Depends(require_auth("metrics", "read")),
):
    """Get SLO compliance data."""
    return data_service.get_slo_compliance()


@router.get("/revenue")
async def get_revenue_impact(
    user: dict = Depends(require_auth("metrics", "read")),
):
    """Get revenue impact data."""
    return data_service.get_revenue_impact()


@router.get("/cost")
async def get_cost_trends(
    user: dict = Depends(require_auth("metrics", "read")),
):
    """Get cost trend data."""
    return {
        "current_hourly_usd": 0,
        "projected_daily_usd": 0,
        "trend": [],
    }


@router.get("/traces")
async def get_traces(
    service: Optional[str] = None,
    user: dict = Depends(require_auth("metrics", "read")),
):
    """Get trace waterfall data for a service."""
    traces = data_service.get_traces(service)
    return {"traces": traces, "total": len(traces)}


@router.get("/profiles")
async def get_profiles(
    entity: Optional[str] = None,
    user: dict = Depends(require_auth("metrics", "read")),
):
    """Get flame graph data for an entity."""
    return {
        "profiles": [],
        "total": 0,
    }


@router.get("/deployments")
async def get_deployments(
    user: dict = Depends(require_auth("metrics", "read")),
):
    """Get deployment timeline data."""
    deployments = data_service.get_deployments()
    return {"deployments": deployments, "total": len(deployments)}
