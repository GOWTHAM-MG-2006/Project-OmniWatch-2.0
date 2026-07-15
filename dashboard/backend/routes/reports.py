"""OmniWatch 2.0 — NexusUX: Reports Route"""

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

class ReportResponse(BaseModel):
    report_id: str
    report_type: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int


class ComplianceReportRequest(BaseModel):
    report_type: str  # soc2, iso27001
    lookback_days: Optional[int] = 30


class MTTRReportResponse(BaseModel):
    mttr_minutes: float
    trend: List[Any]
    period: str


# ─── Endpoints (static routes BEFORE parameterized routes) ─────────

@router.get("/", response_model=ReportListResponse)
async def list_reports(
    report_type: Optional[str] = None,
    user: dict = Depends(require_auth("reports", "read")),
):
    """List available reports."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="report",
        resource_id=None,
        action="list",
        outcome="success",
        metadata={"report_type": report_type},
    )
    return {"reports": [], "total": 0}


@router.get("/mttr", response_model=MTTRReportResponse)
async def get_mttr_report(
    user: dict = Depends(require_auth("reports", "read")),
):
    """Get Mean Time to Resolution report."""
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="report",
        resource_id=None,
        action="mttr",
        outcome="success",
    )
    return data_service.get_mttr()


@router.post("/compliance", response_model=ReportResponse, status_code=202)
async def generate_compliance_report(
    data: ComplianceReportRequest,
    user: dict = Depends(require_auth("reports", "write")),
):
    """Generate a compliance report (SOC2/ISO27001)."""
    valid_types = ["soc2", "iso27001"]
    if data.report_type.lower() not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid report type '{data.report_type}'. Valid types: {valid_types}")
    if data.lookback_days and (data.lookback_days < 1 or data.lookback_days > 365):
        raise HTTPException(status_code=400, detail="lookback_days must be between 1 and 365")
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="report",
        resource_id=None,
        action="generate_compliance",
        outcome="success",
        metadata={"report_type": data.report_type, "lookback_days": data.lookback_days},
    )
    return {"report_id": "RPT-NEW", "status": "generating"}


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    user: dict = Depends(require_auth("reports", "read")),
):
    """Get a specific report."""
    report = None
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    audit_logger.log_event(
        event_type="api_call",
        user_id=user.get("user_id"),
        resource_type="report",
        resource_id=report_id,
        action="get",
        outcome="success",
    )
    return report
