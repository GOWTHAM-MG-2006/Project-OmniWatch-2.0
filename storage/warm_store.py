"""
OmniWatch 2.0 — NexusStore
Component: Warm Store (ClickHouse Client)
Layer: 4
Phase: 1
Purpose: ClickHouse client for warm-tier time-series storage
Inputs: Flushed data from Hot Store, direct writes from StreamForge
Outputs: Queried results for dashboard and AI layers
"""

import os
import json
import logging
from datetime import datetime
from typing import Any

import clickhouse_connect

from storage.query_validator import validate_query

logger = logging.getLogger(__name__)


class WarmStore:
    """ClickHouse client for warm-tier storage."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str = "omniwatch",
    ):
        self.host = host or os.getenv("CLICKHOUSE_HOST", "localhost")
        self.port = port or int(os.getenv("CLICKHOUSE_PORT", "9000"))
        self.database = database
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                database=self.database,
            )
        return self._client

    def insert_metrics(self, records: list[dict[str, Any]]) -> int:
        """Insert metric records into the metrics table."""
        if not records:
            return 0

        columns = ["entity_id", "entity_type", "entity_layer", "metric_name",
                    "metric_value", "metric_unit", "tags", "timestamp"]
        data = [
            [r.get(c) for c in columns]
            for r in records
        ]
        self.client.insert("metrics", data, column_names=columns)
        logger.info("Inserted %d metrics", len(records))
        return len(records)

    def insert_logs(self, records: list[dict[str, Any]]) -> int:
        """Insert log records into the logs table."""
        if not records:
            return 0

        columns = ["entity_id", "entity_type", "service_name", "log_level",
                    "message", "trace_id", "span_id", "attributes", "timestamp"]
        data = [
            [r.get(c) for c in columns]
            for r in records
        ]
        self.client.insert("logs", data, column_names=columns)
        logger.info("Inserted %d logs", len(records))
        return len(records)

    def insert_traces(self, records: list[dict[str, Any]]) -> int:
        """Insert trace records into the traces table."""
        if not records:
            return 0

        columns = ["trace_id", "span_id", "parent_span_id", "service_name",
                    "operation_name", "entity_id", "entity_type", "duration_ms",
                    "status_code", "status_message", "attributes",
                    "start_time", "end_time"]
        data = [
            [r.get(c) for c in columns]
            for r in records
        ]
        self.client.insert("traces", data, column_names=columns)
        logger.info("Inserted %d traces", len(records))
        return len(records)

    def insert_anomalies(self, records: list[dict[str, Any]]) -> int:
        """Insert anomaly records."""
        if not records:
            return 0

        columns = ["anomaly_id", "entity_id", "entity_type", "entity_layer",
                    "metric_name", "anomaly_score", "confidence",
                    "deviation_from_baseline", "status", "topology_context",
                    "created_at"]
        data = [
            [r.get(c) for c in columns]
            for r in records
        ]
        self.client.insert("anomalies", data, column_names=columns)
        logger.info("Inserted %d anomalies", len(records))
        return len(records)

    def insert_incidents(self, records: list[dict[str, Any]]) -> int:
        """Insert incident records."""
        if not records:
            return 0

        columns = ["incident_id", "severity", "business_impact_score",
                    "root_cause", "related_anomaly_ids", "deduplicated_count",
                    "sla_breach_risk", "assigned_to", "status",
                    "created_at", "updated_at"]
        data = [
            [r.get(c) for c in columns]
            for r in records
        ]
        self.client.insert("incidents", data, column_names=columns)
        logger.info("Inserted %d incidents", len(records))
        return len(records)

    def query_metrics(
        self,
        entity_id: str | None = None,
        metric_name: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Query metrics with optional filters."""
        conditions = []
        params: dict[str, Any] = {}

        if entity_id:
            conditions.append("entity_id = {entity_id:String}")
            params["entity_id"] = entity_id
        if metric_name:
            conditions.append("metric_name = {metric_name:String}")
            params["metric_name"] = metric_name
        if start_time:
            conditions.append("timestamp >= {start_time:DateTime64(3, 'UTC')}")
            params["start_time"] = start_time
        if end_time:
            conditions.append("timestamp <= {end_time:DateTime64(3, 'UTC')}")
            params["end_time"] = end_time

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM metrics WHERE {where} ORDER BY timestamp DESC LIMIT {{limit:UInt32}}"
        params["limit"] = limit

        result = self.client.query(query, parameters=params)
        return [dict(zip(result.column_names, row)) for row in result.result_rows]

    def query_logs(
        self,
        entity_id: str | None = None,
        log_level: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Query logs with optional filters."""
        conditions = []
        params: dict[str, Any] = {}

        if entity_id:
            conditions.append("entity_id = {entity_id:String}")
            params["entity_id"] = entity_id
        if log_level:
            conditions.append("log_level = {log_level:String}")
            params["log_level"] = log_level
        if start_time:
            conditions.append("timestamp >= {start_time:DateTime64(3, 'UTC')}")
            params["start_time"] = start_time
        if end_time:
            conditions.append("timestamp <= {end_time:DateTime64(3, 'UTC')}")
            params["end_time"] = end_time

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM logs WHERE {where} ORDER BY timestamp DESC LIMIT {{limit:UInt32}}"
        params["limit"] = limit

        result = self.client.query(query, parameters=params)
        return [dict(zip(result.column_names, row)) for row in result.result_rows]

    def query_traces(
        self,
        trace_id: str | None = None,
        service_name: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Query traces with optional filters."""
        conditions = []
        params: dict[str, Any] = {}

        if trace_id:
            conditions.append("trace_id = {trace_id:String}")
            params["trace_id"] = trace_id
        if service_name:
            conditions.append("service_name = {service_name:String}")
            params["service_name"] = service_name

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM traces WHERE {where} ORDER BY start_time DESC LIMIT {{limit:UInt32}}"
        params["limit"] = limit

        result = self.client.query(query, parameters=params)
        return [dict(zip(result.column_names, row)) for row in result.result_rows]

    def execute(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a validated query (read-only)."""
        if not validate_query(query):
            raise ValueError("Query contains disallowed keywords or is not a read-only statement")
        result = self.client.query(query, parameters=params or {})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]

    def health_check(self) -> bool:
        """Verify ClickHouse connectivity."""
        try:
            result = self.client.query("SELECT 1")
            return result.result_rows[0][0] == 1
        except Exception as e:
            logger.error("ClickHouse health check failed: %s", e)
            return False
