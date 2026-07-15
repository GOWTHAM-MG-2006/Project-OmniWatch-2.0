"""
OmniWatch 2.0 — Continuous Learning
Component: Knowledge Base
Layer: 10
Phase: 4
Purpose: Persistent store of root causes, playbooks, resolution timelines
Input: IncidentRecord outcomes from AutoHeal
Output: Queryable knowledge base (ClickHouse + MinIO)
Technology: Python + clickhouse-connect + minio
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Any

from config import config

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """Persistent incident outcome store backed by ClickHouse and MinIO."""

    def __init__(
        self,
        clickhouse_host: str | None = None,
        clickhouse_port: int | None = None,
        minio_endpoint: str | None = None,
    ):
        self.ch_host = clickhouse_host or config.CLICKHOUSE_HOST
        self.ch_port = int(clickhouse_port or config.CLICKHOUSE_PORT)
        self.minio_endpoint = minio_endpoint or os.getenv("MINIO_ENDPOINT", "localhost:9001")
        self._ch_client = None
        self._minio_client = None

    @property
    def ch(self):
        if self._ch_client is None:
            try:
                import clickhouse_connect
                self._ch_client = clickhouse_connect.get_client(host=self.ch_host, port=self.ch_port)
            except Exception as e:
                logger.warning("ClickHouse unavailable: %s", e)
                self._ch_client = False
        return self._ch_client

    @property
    def minio(self):
        if self._minio_client is None:
            try:
                from minio import Minio
                access_key = os.environ.get("MINIO_ACCESS_KEY")
                secret_key = os.environ.get("MINIO_SECRET_KEY")
                if not access_key or not secret_key:
                    logger.warning("MINIO_ACCESS_KEY/MINIO_SECRET_KEY not set; MinIO unavailable")
                    self._minio_client = False
                    return self._minio_client
                self._minio_client = Minio(
                    self.minio_endpoint,
                    access_key=access_key,
                    secret_key=secret_key,
                    secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
                )
            except Exception as e:
                logger.warning("MinIO unavailable: %s", e)
                self._minio_client = False
        return self._minio_client

    def store_incident_outcome(
        self,
        incident: dict[str, Any],
        action_result: dict[str, Any],
        resolution_notes: str = "",
    ) -> str:
        """Store an incident resolution outcome in the knowledge base.

        Args:
            incident: IncidentRecord dict.
            action_result: ActionResult dict.
            resolution_notes: Free-text notes about the resolution.

        Returns:
            Knowledge base entry ID.
        """
        entry_id = f"KB-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        record = {
            "entry_id": entry_id,
            "incident_id": incident.get("incident_id", ""),
            "severity": incident.get("severity", "P4"),
            "root_cause_entity": incident.get("root_cause", ""),
            "related_anomalies": incident.get("related_anomalies", []),
            "action_type": action_result.get("action_type", ""),
            "action_success": action_result.get("success", False),
            "action_output": action_result.get("output", ""),
            "execution_time_seconds": action_result.get("execution_time_seconds", 0),
            "resolution_notes": resolution_notes,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }

        if self.ch:
            try:
                self.ch.insert(
                    "omniwatch.knowledge_base",
                    [record],
                    column_names=list(record.keys()),
                )
                logger.info("Stored KB entry: %s", entry_id)
            except Exception as e:
                logger.error("Failed to store KB entry: %s", e)

        return entry_id

    def query_by_entity(self, entity_type: str, limit: int = 50) -> list[dict[str, Any]]:
        """Query knowledge base by root cause entity type.

        Args:
            entity_type: Entity type to filter (e.g., "Database", "Service").
            limit: Maximum results.

        Returns:
            List of matching knowledge base entries.
        """
        if not self.ch:
            return []

        try:
            result = self.ch.query(
                "SELECT * FROM omniwatch.knowledge_base "
                "WHERE root_cause_entity LIKE {etype:String} "
                "ORDER BY stored_at DESC LIMIT {lim:Int32}",
                parameters={"etype": f"%{entity_type}%", "lim": limit},
            )
            return [dict(zip(result.column_names, row)) for row in result.result_rows]
        except Exception as e:
            logger.error("KB query failed: %s", e)
            return []

    def query_successful_actions(self, action_type: str, limit: int = 20) -> list[dict[str, Any]]:
        """Query knowledge base for successful actions of a given type.

        Args:
            action_type: Action type to filter (e.g., "rollback", "restart_pod").
            limit: Maximum results.

        Returns:
            List of successful KB entries.
        """
        if not self.ch:
            return []

        try:
            result = self.ch.query(
                "SELECT * FROM omniwatch.knowledge_base "
                "WHERE action_type = {atype:String} AND action_success = true "
                "ORDER BY stored_at DESC LIMIT {lim:Int32}",
                parameters={"atype": action_type, "lim": limit},
            )
            return [dict(zip(result.column_names, row)) for row in result.result_rows]
        except Exception as e:
            logger.error("KB query failed: %s", e)
            return []

    def get_resolution_stats(self) -> dict[str, Any]:
        """Get aggregate resolution statistics from the knowledge base.

        Returns:
            Dict with total incidents, success rate, avg execution time.
        """
        if not self.ch:
            return {"total": 0, "success_rate": 0, "avg_execution_time": 0}

        try:
            result = self.ch.query(
                "SELECT "
                "count() as total, "
                "sum(CASE WHEN action_success THEN 1 ELSE 0 END) as successes, "
                "avg(execution_time_seconds) as avg_time "
                "FROM omniwatch.knowledge_base"
            )
            row = result.first_row
            total = row[0] or 0
            successes = row[1] or 0
            avg_time = row[2] or 0
            return {
                "total": total,
                "success_rate": round(successes / total, 3) if total > 0 else 0,
                "avg_execution_time": round(avg_time, 2),
            }
        except Exception as e:
            logger.error("KB stats query failed: %s", e)
            return {"total": 0, "success_rate": 0, "avg_execution_time": 0}
