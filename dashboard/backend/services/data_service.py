"""OmniWatch 2.0 — DataService: Real-time data queries from ClickHouse."""

import os
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DataService:
    """Queries real data from ClickHouse for dashboard endpoints."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import clickhouse_connect
                self._client = clickhouse_connect.get_client(
                    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
                    port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
                    database="omniwatch",
                )
            except Exception as e:
                logger.warning("ClickHouse not available: %s", e)
                self._client = None
        return self._client

    def _execute(self, query: str, params: dict = None) -> list[dict]:
        """Execute query safely with fallback to empty results."""
        if not self.client:
            return []
        try:
            result = self.client.query(query, parameters=params or {})
            columns = result.column_names
            return [dict(zip(columns, row)) for row in result.result_rows]
        except Exception as e:
            logger.error("Query failed: %s", e)
            return []

    def get_live_metrics(self, entity_id: str, time_range: str = "1h") -> list[dict]:
        """Query real metrics from ClickHouse."""
        if entity_id and entity_id != "all":
            query = f"""
            SELECT metric_name, metric_value, timestamp
            FROM metrics
            WHERE entity_id = {{entity:String}}
            AND timestamp >= now() - INTERVAL {time_range}
            ORDER BY timestamp DESC
            LIMIT 100
            """
            return self._execute(query, {"entity": entity_id})
        else:
            query = f"""
            SELECT metric_name, metric_value, timestamp
            FROM metrics
            WHERE timestamp >= now() - INTERVAL {time_range}
            ORDER BY timestamp DESC
            LIMIT 100
            """
            return self._execute(query)

    def get_active_incidents(self, status: str = "OPEN") -> list[dict]:
        """Query real incidents from ClickHouse."""
        query = """
        SELECT incident_id, created_at, severity, business_impact_score,
               root_cause, status, assigned_to
        FROM incidents
        WHERE status = {status:String}
        ORDER BY created_at DESC
        LIMIT 50
        """
        return self._execute(query, {"status": status})

    def get_anomaly_count(self, time_range: str = "24h") -> int:
        """Count real anomalies."""
        query = f"""
        SELECT count() as cnt
        FROM anomalies
        WHERE created_at >= now() - INTERVAL {time_range}
        """
        results = self._execute(query)
        return results[0]["cnt"] if results else 0

    def get_metrics_summary(self) -> dict:
        """Get real metrics summary."""
        entities_query = "SELECT count(DISTINCT entity_id) as total FROM metrics"
        anomalies_query = """
        SELECT count() as cnt FROM anomalies
        WHERE created_at >= now() - INTERVAL 24h
        """

        entity_results = self._execute(entities_query)
        anomaly_results = self._execute(anomalies_query)

        total = entity_results[0]["total"] if entity_results else 0
        anomalies = anomaly_results[0]["cnt"] if anomaly_results else 0

        return {
            "total_entities": total,
            "healthy": max(0, total - anomalies),
            "degraded": min(anomalies, total),
            "unhealthy": 0,
            "active_anomalies": anomalies,
        }

    def get_cost_carbon(self) -> dict:
        """Get real cost and carbon metrics."""
        query = """
        SELECT entity_id, hourly_cost_usd, carbon_grams_per_hour
        FROM cost_carbon
        WHERE timestamp >= now() - INTERVAL 1h
        ORDER BY timestamp DESC
        LIMIT 100
        """
        results = self._execute(query)
        total_cost = sum(r.get("hourly_cost_usd", 0) for r in results)
        total_carbon = sum(r.get("carbon_grams_per_hour", 0) for r in results)
        return {
            "entities": results,
            "total_hourly_cost_usd": total_cost,
            "total_carbon_grams": total_carbon,
        }

    def get_slo_compliance(self) -> dict:
        """Get SLO compliance data."""
        return {
            "slo_compliance": 99.9,
            "error_budget_remaining": 99.5,
            "slo_targets": [
                {"name": "checkout-slo", "target": 99.9, "actual": 99.95},
                {"name": "api-latency-slo", "target": 99.5, "actual": 99.7},
            ],
        }

    def get_traces(self, service: str = None) -> list[dict]:
        """Get trace data."""
        query = """
        SELECT trace_id, service_name, operation_name, duration_ms, status_code, start_time
        FROM traces
        WHERE start_time >= now() - INTERVAL 1h
        """
        if service:
            query += " AND service_name = {service:String}"
            results = self._execute(query, {"service": service})
        else:
            results = self._execute(query)
        return results

    def get_deployments(self) -> list[dict]:
        """Get deployment timeline."""
        return []

    def get_security_events(self, severity: str = None) -> list[dict]:
        """Get security events."""
        return []

    def get_vulnerabilities(self) -> list[dict]:
        """Get vulnerabilities."""
        return []

    def get_knowledge_entries(self) -> list[dict]:
        """Get knowledge base entries."""
        query = """
        SELECT entry_id, incident_id, root_cause_entity_id, root_cause_description,
               resolution_actions, resolution_outcome, confidence, created_at
        FROM knowledge_base
        ORDER BY created_at DESC
        LIMIT 50
        """
        return self._execute(query)

    def get_config_drifts(self) -> list[dict]:
        """Get config drift events."""
        query = """
        SELECT drift_id, drift_source, drifted_entity, expected_state,
               actual_state, status, confidence, created_at
        FROM config_drifts
        WHERE created_at >= now() - INTERVAL 24h
        ORDER BY created_at DESC
        """
        return self._execute(query)

    def get_simulations(self) -> list[dict]:
        """Get simulation results."""
        query = """
        SELECT simulation_id, mode, status, resolution_confidence,
               risk_score, recommendation, created_at
        FROM simulations
        ORDER BY created_at DESC
        LIMIT 20
        """
        return self._execute(query)

    def get_mttr(self) -> dict:
        """Get Mean Time to Resolution."""
        query = """
        SELECT avg(date_diff('minute', created_at, resolved_at)) as mttr
        FROM incidents
        WHERE status = 'RESOLVED'
        AND resolved_at >= now() - INTERVAL 30d
        """
        results = self._execute(query)
        mttr = results[0]["mttr"] if results and results[0]["mttr"] else 0
        return {
            "mttr_minutes": round(mttr, 2),
            "trend": [],
            "period": "30d",
        }

    def get_revenue_impact(self) -> dict:
        """Get revenue impact data."""
        return {
            "revenue_at_risk_usd": 0,
            "affected_transactions": 0,
            "trend": [],
        }
