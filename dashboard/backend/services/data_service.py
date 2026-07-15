"""OmniWatch 2.0 — DataService: Real-time data queries from ClickHouse."""

import os
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from config import config

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
                    host=config.CLICKHOUSE_HOST,
                    port=config.CLICKHOUSE_PORT,
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
        """Get real SLO compliance data from ClickHouse."""
        query = """
        SELECT entity_id, slo_name, target_value, current_value,
               breach, error_budget_remaining
        FROM slo_targets
        WHERE timestamp >= now() - INTERVAL 1 hour
        ORDER BY timestamp DESC
        """
        results = self._execute(query)
        if results:
            avg_compliance = sum(r.get("current_value", 0) for r in results) / len(results)
            avg_budget = sum(r.get("error_budget_remaining", 100) for r in results) / len(results)
            return {
                "slo_compliance": round(avg_compliance, 2),
                "error_budget_remaining": round(avg_budget, 2),
                "slo_targets": results,
            }
        return {
            "slo_compliance": 0,
            "error_budget_remaining": 0,
            "slo_targets": [],
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
        """Get deployment timeline from ClickHouse."""
        query = """
        SELECT deployment_id, service_name, version, commit_sha,
               deployed_at, deployed_by, status
        FROM deployments
        ORDER BY deployed_at DESC
        LIMIT 50
        """
        return self._execute(query)

    def get_security_events(self, severity: str = None) -> list[dict]:
        """Get security events from ClickHouse."""
        if severity:
            query = """
            SELECT event_id, attack_type, entity_id, severity, confidence,
                   source_ip, recommended_action, timestamp
            FROM security_events
            WHERE severity = {severity:String}
            AND timestamp >= now() - INTERVAL 24h
            ORDER BY timestamp DESC
            LIMIT 50
            """
            return self._execute(query, {"severity": severity})
        else:
            query = """
            SELECT event_id, attack_type, entity_id, severity, confidence,
                   source_ip, recommended_action, timestamp
            FROM security_events
            WHERE timestamp >= now() - INTERVAL 24h
            ORDER BY timestamp DESC
            LIMIT 50
            """
            return self._execute(query)

    def get_vulnerabilities(self) -> list[dict]:
        """Get vulnerabilities from ClickHouse."""
        query = """
        SELECT vulnerability_id, entity_id, cve_id, severity, cvss_score,
               affected_package, reachability, remediation, fixed, timestamp
        FROM vulnerabilities
        WHERE fixed = false
        ORDER BY cvss_score DESC
        LIMIT 50
        """
        return self._execute(query)

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
        """Get real revenue impact from ClickHouse."""
        query = """
        SELECT entity_id,
               SUM(business_impact_score) as total_impact,
               COUNT(*) as incident_count
        FROM incidents
        WHERE status = 'OPEN'
        GROUP BY entity_id
        ORDER BY total_impact DESC
        """
        results = self._execute(query)
        total_revenue = sum(r.get("total_impact", 0) for r in results)
        total_users = sum(r.get("incident_count", 0) for r in results)
        return {
            "revenue_at_risk_usd": total_revenue,
            "affected_transactions": total_users,
            "entities": results,
            "trend": [],
        }

    def search_knowledge(self, search_term: str) -> list[dict]:
        """Search knowledge base entries."""
        query = """
        SELECT entry_id, incident_id, root_cause_entity_id, root_cause_description,
               resolution_actions, resolution_outcome, confidence, created_at
        FROM knowledge_base
        WHERE root_cause_description LIKE {term:String}
           OR root_cause_entity_id LIKE {term:String}
           OR resolution_actions LIKE {term:String}
        ORDER BY created_at DESC
        LIMIT 20
        """
        return self._execute(query, {"term": f"%{search_term}%"})

    def get_knowledge_entry(self, entry_id: str) -> dict | None:
        """Get a specific knowledge base entry."""
        query = """
        SELECT entry_id, incident_id, root_cause_entity_id, root_cause_description,
               resolution_actions, resolution_outcome, confidence, created_at
        FROM knowledge_base
        WHERE entry_id = {entry_id:String}
        """
        results = self._execute(query, {"entry_id": entry_id})
        return results[0] if results else None

    def get_incident(self, incident_id: str) -> dict | None:
        """Get a specific incident."""
        query = """
        SELECT incident_id, created_at, severity, business_impact_score,
               root_cause, status, assigned_to, blast_radius
        FROM incidents
        WHERE incident_id = {incident_id:String}
        """
        results = self._execute(query, {"incident_id": incident_id})
        return results[0] if results else None

    def get_simulation(self, simulation_id: str) -> dict | None:
        """Get a specific simulation."""
        query = """
        SELECT simulation_id, mode, status, resolution_confidence,
               risk_score, recommendation, created_at
        FROM simulations
        WHERE simulation_id = {sim_id:String}
        """
        results = self._execute(query, {"sim_id": simulation_id})
        return results[0] if results else None

    def get_config_drift(self, drift_id: str) -> dict | None:
        """Get a specific config drift."""
        query = """
        SELECT drift_id, drift_source, drifted_entity, expected_state,
               actual_state, status, confidence, created_at
        FROM config_drifts
        WHERE drift_id = {drift_id:String}
        """
        results = self._execute(query, {"drift_id": drift_id})
        return results[0] if results else None
