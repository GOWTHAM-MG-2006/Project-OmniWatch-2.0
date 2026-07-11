"""OmniWatch 2.0 — NexusUX: Audit Route"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from auth.middleware import require_auth
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
    user: dict = Depends(require_auth("audit", "read")),
):
    """Query audit logs with optional filters. Admin only."""
    if "admin" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin access required")
    events = audit_logger.query_events(
        start_date=start_date, end_date=end_date,
        event_type=event_type, user_id=user_id, limit=limit,
    )
    return {"events": events, "total": len(events)}


@router.get("/stats")
async def audit_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(require_auth("audit", "read")),
):
    """Get audit event counts by event type. Admin only."""
    if "admin" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin access required")
    stats = audit_logger.get_stats(start_date=start_date, end_date=end_date)
    return {"stats": stats, "total_events": sum(stats.values())}
