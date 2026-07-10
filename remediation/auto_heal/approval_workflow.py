"""
OmniWatch 2.0 — AutoHeal
Component: Approval Workflow
Layer: 7
Phase: 3
Purpose: Human-in-the-loop approval for medium-confidence incidents
Inputs: IncidentRecord with medium confidence
Outputs: Approval request written to ClickHouse pending_approvals table
Technology: Python + clickhouse-connect
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class ApprovalWorkflow:
    """Manages human approval workflow for remediation actions."""

    def __init__(
        self,
        clickhouse_host: str | None = None,
        clickhouse_port: int | None = None,
    ):
        self.ch_host = clickhouse_host or os.getenv("CLICKHOUSE_HOST", "localhost")
        self.ch_port = int(clickhouse_port or os.getenv("CLICKHOUSE_PORT", "9000"))
        self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            try:
                import clickhouse_connect
                self._conn = clickhouse_connect.get_client(
                    host=self.ch_host, port=self.ch_port,
                )
            except Exception as e:
                logger.warning("ClickHouse unavailable: %s", e)
                self._conn = False
        return self._conn

    def create_approval_request(
        self,
        incident: dict[str, Any],
        proposed_action: dict[str, Any],
        policy_decision: dict[str, Any],
    ) -> dict[str, Any]:
        """Create an approval request for a remediation action.

        Args:
            incident: IncidentRecord dict.
            proposed_action: Action to be approved.
            policy_decision: Output from PolicyEngine.

        Returns:
            Approval request dict with request_id.
        """
        request_id = f"APR-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        request = {
            "request_id": request_id,
            "incident_id": incident.get("incident_id", ""),
            "severity": incident.get("severity", "P4"),
            "proposed_action": proposed_action,
            "policy_reason": policy_decision.get("reason", ""),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": "",
            "approved_by": None,
            "approved_at": None,
        }

        if self.conn:
            try:
                self.conn.insert(
                    "omniwatch.pending_approvals",
                    [request],
                    column_names=["request_id", "incident_id", "severity", "proposed_action",
                                   "policy_reason", "status", "created_at", "expires_at",
                                   "approved_by", "approved_at"],
                )
                logger.info("Approval request created: %s", request_id)
            except Exception as e:
                logger.error("Failed to write approval request: %s", e)

        return request

    def approve_request(
        self, request_id: str, approver: str, decision: str = "approved",
    ) -> bool:
        """Approve or reject a pending request.

        Args:
            request_id: The approval request ID.
            approver: Who approved/rejected.
            decision: "approved" or "rejected".

        Returns:
            True if updated successfully.
        """
        if not self.conn:
            logger.warning("ClickHouse unavailable — cannot update approval")
            return False

        try:
            self.conn.command(
                "ALTER TABLE omniwatch.pending_approvals UPDATE "
                "status = {status:String}, approved_by = {approver:String}, "
                "approved_at = {now:String} "
                "WHERE request_id = {req:String}",
                parameters={
                    "status": decision,
                    "approver": approver,
                    "now": datetime.now(timezone.utc).isoformat(),
                    "req": request_id,
                },
            )
            logger.info("Approval %s: %s by %s", request_id, decision, approver)
            return True
        except Exception as e:
            logger.error("Failed to update approval %s: %s", request_id, e)
            return False

    def get_pending_requests(self) -> list[dict[str, Any]]:
        """Get all pending approval requests."""
        if not self.conn:
            return []

        try:
            result = self.conn.query(
                "SELECT * FROM omniwatch.pending_approvals WHERE status = 'pending' "
                "ORDER BY created_at DESC"
            )
            return [dict(zip(result.column_names, row)) for row in result.result_rows]
        except Exception as e:
            logger.error("Failed to query pending approvals: %s", e)
            return []
