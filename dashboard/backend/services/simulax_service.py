"""SimulaX Service — Digital Twin simulation engine.
Uses real topology data from GraphStore, real metrics from ClickHouse,
and deterministic simulation models (not random).
"""
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Optional

from config import config

logger = logging.getLogger(__name__)


class SimulaXService:
    """Runs real SimulaX simulations with deterministic models."""

    def __init__(self, clickhouse_client=None):
        self._client = clickhouse_client

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
                logger.warning("ClickHouse not available for SimulaX: %s", e)
                self._client = None
        return self._client

    def run_remediation_sim(self, action_type: str, entity_id: str,
                            current_state: dict) -> dict:
        """Simulate a remediation action using historical success rates."""
        sim_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"

        success_rate = 0.85
        avg_duration = 300

        if self.client:
            try:
                query = """
                    SELECT action_type,
                           countIf(status='SUCCESS') as successes,
                           count(*) as total,
                           avg(duration_seconds) as avg_duration
                    FROM remediation_history
                    WHERE action_type = {at:String}
                    GROUP BY action_type
                """
                result = self.client.query(query, parameters={"at": action_type})
                if result.row_count > 0:
                    row = result.first_row
                    success_rate = row[1] / row[2] if row[2] > 0 else 0.85
                    avg_duration = row[3] if row[3] else 300
            except Exception as e:
                logger.warning("Failed to query remediation history: %s", e)

        severity = current_state.get("severity", "P2")
        severity_risk = {"P1": 0.3, "P2": 0.2, "P3": 0.1, "P4": 0.05}
        risk_score = severity_risk.get(severity, 0.15)

        side_effects = []
        if risk_score > 0.15:
            side_effects = [
                "Potential brief latency spike on dependent services",
                f"Estimated recovery window: {int(avg_duration * 0.1)}s"
            ]

        confidence = round(min(0.99, success_rate * (1 - risk_score)), 2)

        return {
            "simulation_id": sim_id,
            "action_type": action_type,
            "entity_id": entity_id,
            "confidence": confidence,
            "estimated_recovery_minutes": round(avg_duration / 60, 1),
            "risk_score": round(risk_score, 2),
            "side_effects": side_effects,
            "historical_success_rate": round(success_rate, 2),
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }

    def run_capacity_sim(self, entity_id: str, proposed_config: dict,
                         current_metrics: dict) -> dict:
        """Simulate capacity changes using real current metrics."""
        sim_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"

        current_cpu = current_metrics.get("cpu_percent", 50)
        current_memory = current_metrics.get("memory_percent", 60)
        proposed_cpu = proposed_config.get("cpu_limit", current_cpu)
        proposed_memory = proposed_config.get("memory_limit", current_memory)

        cpu_headroom = max(0, proposed_cpu - current_cpu)
        memory_headroom = max(0, proposed_memory - current_memory)

        growth_rate = current_metrics.get("growth_rate_per_hour", 2.0)
        saturation_point = min(proposed_cpu, proposed_memory)
        current_usage = max(current_cpu, current_memory)

        if growth_rate > 0:
            hours_to_exhaustion = (saturation_point - current_usage) / growth_rate
        else:
            hours_to_exhaustion = float('inf')

        actions = []
        if current_cpu > 80:
            actions.append("Scale CPU before saturation")
        if current_memory > 80:
            actions.append("Scale memory before OOM")
        if not actions:
            actions.append("Current resources adequate — no action needed")

        return {
            "simulation_id": sim_id,
            "entity_id": entity_id,
            "cpu_headroom_percent": round(cpu_headroom, 1),
            "memory_headroom_percent": round(memory_headroom, 1),
            "hours_to_cpu_exhaustion": round(hours_to_exhaustion, 1),
            "recommended_actions": actions,
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }

    def run_deployment_sim(self, entity_id: str, new_version: str,
                           current_state: dict) -> dict:
        """Simulate deployment risk based on change magnitude."""
        sim_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"

        current_version = current_state.get("current_version", "0.0.0")
        test_coverage = current_state.get("test_coverage_percent", 50)
        recent_incidents = current_state.get("recent_incidents_24h", 0)

        version_parts_current = [int(x) for x in current_version.split(".") if x.isdigit()]
        version_parts_new = [int(x) for x in new_version.split(".") if x.isdigit()]
        change_magnitude = 0
        for i in range(max(len(version_parts_current), len(version_parts_new))):
            old = version_parts_current[i] if i < len(version_parts_current) else 0
            new = version_parts_new[i] if i < len(version_parts_new) else 0
            change_magnitude += abs(new - old)

        risk_score = min(1.0, (change_magnitude * 0.1) +
                         (100 - test_coverage) * 0.005 +
                         recent_incidents * 0.05)

        if risk_score > 0.7:
            recommendation = "BLOCK"
            reason = "High risk — insufficient test coverage and recent incidents"
        elif risk_score > 0.4:
            recommendation = "MODIFY"
            reason = "Moderate risk — consider staged rollout or additional tests"
        else:
            recommendation = "PROCEED"
            reason = "Low risk — changes are small and well-tested"

        slo_impact = round(max(0, (1 - test_coverage / 100) * 0.5), 2)

        return {
            "simulation_id": sim_id,
            "entity_id": entity_id,
            "from_version": current_version,
            "to_version": new_version,
            "risk_score": round(risk_score, 2),
            "slo_impact_percent": slo_impact,
            "recommendation": recommendation,
            "reason": reason,
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }

    def run_chaos_sim(self, entity_id: str, fault_type: str,
                      blast_radius_limit: int = 10) -> dict:
        """Simulate chaos by querying real topology for blast radius."""
        sim_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"

        affected_entities = [entity_id]

        if self.client:
            try:
                query = """
                    SELECT source_entity_id, target_entity_id, relationship_type
                    FROM topology_edges
                    WHERE source_entity_id = {eid:String}
                    OR target_entity_id = {eid:String}
                """
                result = self.client.query(query, parameters={"eid": entity_id})
                for row in result.result_rows:
                    other = row[1] if row[0] == entity_id else row[0]
                    if other not in affected_entities:
                        affected_entities.append(other)
                affected_entities = affected_entities[:blast_radius_limit]
            except Exception as e:
                logger.warning("Failed to query topology for chaos sim: %s", e)

        cascade_probability = min(1.0, len(affected_entities) * 0.1)

        return {
            "simulation_id": sim_id,
            "fault_type": fault_type,
            "target_entity": entity_id,
            "affected_entities": affected_entities,
            "blast_radius": len(affected_entities),
            "cascade_probability": round(cascade_probability, 2),
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }
