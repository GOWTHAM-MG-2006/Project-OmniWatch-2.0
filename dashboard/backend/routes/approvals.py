"""OmniWatch 2.0 — NexusUX: Approvals Route"""

import os
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


class ApprovalResponse(BaseModel):
    approval_id: str
    action_type: str
    entity_id: str
    risk_score: Optional[float] = None
    status: str
    created_at: Optional[datetime] = None


class ApprovalListResponse(BaseModel):
    approvals: List[ApprovalResponse]
    total: int


class ApprovalActionRequest(BaseModel):
    reason: Optional[str] = None


@router.get("/", response_model=ApprovalListResponse)
async def list_pending_approvals(
    user: dict = Depends(require_auth("approvals", "read")),
):
    """List all pending approvals from ClickHouse."""
    query = """
    SELECT approval_id, action_type, entity_id, risk_score, status, created_at
    FROM pending_approvals
    WHERE status = 'pending'
    ORDER BY created_at DESC
    """
    approvals = data_service._execute(query)
    return {"approvals": approvals, "total": len(approvals)}


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: str,
    user: dict = Depends(require_auth("approvals", "read")),
):
    """Get a specific approval."""
    query = """
    SELECT approval_id, action_type, entity_id, risk_score, status, created_at
    FROM pending_approvals
    WHERE approval_id = {id:String}
    """
    results = data_service._execute(query, {"id": approval_id})
    if not results:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    return results[0]


@router.post("/{approval_id}/approve")
async def approve_action(
    approval_id: str,
    data: ApprovalActionRequest = None,
    user: dict = Depends(require_auth("approvals", "write")),
):
    """Approve an action."""
    user_id = user.get("user_id", "unknown")
    query = """
    SELECT approval_id, action_type, entity_id, risk_score, status
    FROM pending_approvals
    WHERE approval_id = {id:String} AND status = 'pending'
    """
    results = data_service._execute(query, {"id": approval_id})
    if not results:
        raise HTTPException(status_code=404, detail=f"Pending approval {approval_id} not found")

    update_query = """
    ALTER TABLE pending_approvals UPDATE
        status = 'approved',
        approved_by = {user:String},
        approved_at = now()
    WHERE approval_id = {id:String}
    """
    data_service._execute(update_query, {"id": approval_id, "user": user_id})

    audit_logger.log_event(
        event_type="approval",
        user_id=user_id,
        resource_type="approval",
        action="approve",
        outcome="success",
        resource_id=approval_id,
    )

    return {"approval_id": approval_id, "status": "approved", "approved_by": user_id}


@router.post("/{approval_id}/reject")
async def reject_action(
    approval_id: str,
    data: ApprovalActionRequest = None,
    user: dict = Depends(require_auth("approvals", "write")),
):
    """Reject an action."""
    user_id = user.get("user_id", "unknown")
    query = """
    SELECT approval_id, status
    FROM pending_approvals
    WHERE approval_id = {id:String} AND status = 'pending'
    """
    results = data_service._execute(query, {"id": approval_id})
    if not results:
        raise HTTPException(status_code=404, detail=f"Pending approval {approval_id} not found")

    update_query = """
    ALTER TABLE pending_approvals UPDATE
        status = 'rejected',
        rejected_by = {user:String},
        rejected_at = now()
    WHERE approval_id = {id:String}
    """
    data_service._execute(update_query, {"id": approval_id, "user": user_id})

    audit_logger.log_event(
        event_type="approval",
        user_id=user_id,
        resource_type="approval",
        action="reject",
        outcome="success",
        resource_id=approval_id,
    )

    return {"approval_id": approval_id, "status": "rejected", "rejected_by": user_id}
