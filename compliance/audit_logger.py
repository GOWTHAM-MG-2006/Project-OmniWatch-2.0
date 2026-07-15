"""
OmniWatch 2.0 — Compliance
Component: Audit Logger
Layer: Enterprise (Phase 6)
Purpose: Comprehensive audit logging for ALL system actions with ClickHouse append-only storage
Inputs: API calls, remediation actions, config changes, login/logout, policy evaluations
Outputs: Append-only audit_log records in ClickHouse, query results, event statistics
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import clickhouse_connect


class AuditLogger:
    """Append-only audit logger backed by ClickHouse.

    Logs every system action: API calls, remediation actions, config changes,
    login/logout events, and policy evaluations.
    """

    def __init__(self):
        self._client = None
        self._host = os.getenv("CLICKHOUSE_HOST", "clickhouse")
        self._port = int(os.getenv("CLICKHOUSE_PORT", "9000"))
        self._database = os.getenv("CLICKHOUSE_DATABASE", "omniwatch")
        self._table = "audit_log"
        self._retention_years = int(os.getenv("AUDIT_LOG_RETENTION_YEARS", "7"))

    def _get_client(self):
        """Lazy-initialize ClickHouse client."""
        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self._host,
                port=self._port,
            )
        return self._client

    def log_event(
        self,
        event_type: str,
        user_id: str,
        resource_type: str,
        action: str,
        outcome: str,
        resource_id: Optional[str] = None,
        ip_address: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Log an audit event to ClickHouse.

        Args:
            event_type: Category of event (api_call, remediation_action, config_change,
                       login, logout, policy_evaluation)
            user_id: Identifier of the user or system component
            resource_type: Type of resource (endpoint, deployment, service, policy, etc.)
            resource_id: Identifier of the affected resource
            action: Action performed (GET, POST, ROLLBACK, UPDATE, EVALUATE, etc.)
            outcome: Result of the action (success, failure, denied, etc.)
            ip_address: Client IP address (optional)
            metadata: Additional context as JSON-serializable dict (optional)

        Returns:
            The generated event_id.
        """
        client = self._get_client()
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        metadata_json = json.dumps(metadata or {})

        row = [
            event_id,
            event_type or "",
            user_id or "",
            resource_type or "",
            resource_id or "",
            action or "",
            outcome or "",
            metadata_json or "{}",
            ip_address or "",
            timestamp,
        ]

        client.insert(
            f"{self._database}.{self._table}",
            [row],
            column_names=[
                "event_id",
                "event_type",
                "user_id",
                "resource_type",
                "resource_id",
                "action",
                "outcome",
                "metadata",
                "ip_address",
                "timestamp",
            ],
        )

        return event_id

    def query_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query audit events with optional filters.

        Args:
            start_date: Start date filter (YYYY-MM-DD format)
            end_date: End date filter (YYYY-MM-DD format)
            event_type: Filter by event type
            user_id: Filter by user ID
            limit: Maximum number of results (default 100)

        Returns:
            List of audit event dictionaries.
        """
        client = self._get_client()

        conditions = []
        params: dict[str, Any] = {}

        if start_date:
            conditions.append("timestamp >= %(start_date)s")
            params["start_date"] = start_date
        if end_date:
            conditions.append("timestamp < %(end_date)s + INTERVAL 1 DAY")
            params["end_date"] = end_date
        if event_type:
            conditions.append("event_type = %(event_type)s")
            params["event_type"] = event_type
        if user_id:
            conditions.append("user_id = %(user_id)s")
            params["user_id"] = user_id

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT event_id, event_type, user_id, resource_type, resource_id,
                   action, outcome, metadata, ip_address, timestamp
            FROM {self._database}.{self._table}
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT {limit}
        """

        result = client.query(query, parameters=params if params else None)

        events = []
        for row in result.result_rows:
            events.append({
                "event_id": row[0],
                "event_type": row[1],
                "user_id": row[2],
                "resource_type": row[3],
                "resource_id": row[4],
                "action": row[5],
                "outcome": row[6],
                "metadata": row[7],
                "ip_address": row[8],
                "timestamp": row[9],
            })

        return events

    def get_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, int]:
        """Get event counts by event type.

        Args:
            start_date: Optional start date filter (YYYY-MM-DD format)
            end_date: Optional end date filter (YYYY-MM-DD format)

        Returns:
            Dictionary mapping event_type to count.
        """
        client = self._get_client()

        conditions = []
        params: dict[str, Any] = {}

        if start_date:
            conditions.append("timestamp >= %(start_date)s")
            params["start_date"] = start_date
        if end_date:
            conditions.append("timestamp < %(end_date)s + INTERVAL 1 DAY")
            params["end_date"] = end_date

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT event_type, count() as cnt
            FROM {self._database}.{self._table}
            {where_clause}
            GROUP BY event_type
            ORDER BY cnt DESC
        """

        result = client.query(query, parameters=params if params else None)

        return {row[0]: row[1] for row in result.result_rows}
