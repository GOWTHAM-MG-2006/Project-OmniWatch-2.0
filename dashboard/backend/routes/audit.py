"""
OmniWatch 2.0 — NexusUX
Component: Audit Route
Layer: 11
Phase: 6
Purpose: API endpoints for querying audit logs and statistics
Inputs: HTTP requests with date/event/user filters
Outputs: Audit log records, event statistics
"""

from fastapi import APIRouter
from typing import Optional

from compliance.audit_logger import AuditLogger

router = APIRouter()
audit_logger = AuditLogger()


@router.get("/")
async def query_audit_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
):
    """Query audit logs with optional filters."""
    events = audit_logger.query_events(
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        user_id=user_id,
        limit=limit,
    )
    return {"events": events, "total": len(events)}


@router.get("/stats")
async def audit_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get audit event counts by event type."""
    stats = audit_logger.get_stats(start_date=start_date, end_date=end_date)
    return {"stats": stats, "total_events": sum(stats.values())}
