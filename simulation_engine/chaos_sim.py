"""
OmniWatch 2.0 — SimulaX
Component: Chaos Simulator
Layer: 8
Phase: 3
Purpose: Simulates failure injection and cascade propagation through topology
Inputs: Failure scenario definition (which entity, what failure, duration)
Outputs: Predicted blast radius + resilience gaps + recovery path
Technology: SimPy
"""

import hashlib
import logging
import random
from datetime import datetime, timezone
from typing import Any

try:
    import simpy
    HAS_SIMPY = True
except ImportError:
    HAS_SIMPY = False

from simulation_engine.digital_twin import DigitalTwin

logger = logging.getLogger(__name__)

FAILURE_TYPES = {
    "pod_crash": {"description": "Pod/container crash", "base_duration_sec": 30, "cascade_probability": 0.3},
    "database_down": {"description": "Database unavailability", "base_duration_sec": 300, "cascade_probability": 0.8},
    "network_partition": {"description": "Network partition between services", "base_duration_sec": 120, "cascade_probability": 0.6},
    "cpu_saturation": {"description": "CPU at 100%", "base_duration_sec": 180, "cascade_probability": 0.4},
    "memory_exhaustion": {"description": "OOM kill", "base_duration_sec": 10, "cascade_probability": 0.2},
    "disk_full": {"description": "Disk space exhausted", "base_duration_sec": 600, "cascade_probability": 0.5},
}


class ChaosSimulator:
    """Simulates failure injection to test system resilience."""

    def __init__(self, twin: DigitalTwin | None = None):
        self.twin = twin or DigitalTwin()

    def simulate(
        self,
        target_entity: str,
        failure_type: str,
        duration_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Simulate a chaos failure scenario.

        Args:
            target_entity: Entity to inject failure into.
            failure_type: Type of failure (from FAILURE_TYPES keys).
            duration_seconds: Override failure duration.

        Returns:
            Chaos simulation result with blast radius and recovery path.
        """
        failure = FAILURE_TYPES.get(failure_type, FAILURE_TYPES["pod_crash"])
        duration = duration_seconds or failure["base_duration_sec"]

        downstream = self.twin.get_downstream(target_entity)
        upstream = self.twin.get_upstream(target_entity)

        if HAS_SIMPY:
            result = self._run_simpy_chaos(target_entity, failure, duration, downstream, upstream)
        else:
            result = self._mock_chaos(target_entity, failure, duration, downstream, upstream)

        downtime = result["estimated_downtime_minutes"]
        risk_score = min(1.0, len(result["blast_radius"]) * 0.2 + len(result["resilience_gaps"]) * 0.15)

        side_effects = [b["impact"] for b in result["blast_radius"] if b["entity"] != target_entity]
        side_effects.extend(result["resilience_gaps"])

        return {
            "simulation_id": f"CHAOS-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            "mode": "CHAOS_SIMULATION",
            "proposed_action": {"type": "FAILURE_INJECTION", "target": target_entity, "failure_type": failure_type, "duration_seconds": duration},
            "predicted_outcome": {
                "resolution_confidence": max(0.1, 1.0 - risk_score),
                "recovery_time_minutes": downtime,
                "side_effects": side_effects,
                "revenue_recovery_usd": 0,
            },
            "risk_score": round(risk_score, 2),
            "recommendation": "DO_NOT_PROCEED" if risk_score > 0.6 else "PROCEED",
            "blast_radius": result["blast_radius"],
            "resilience_gaps": result["resilience_gaps"],
            "recovery_path": result["recovery_path"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _run_simpy_chaos(
        self, target: str, failure: dict, duration: int,
        downstream: list[str], upstream: list[str],
    ) -> dict[str, Any]:
        """Run SimPy chaos simulation."""
        env = simpy.Environment()
        cascade_prob = failure["cascade_probability"]

        blast_radius = [{"entity": target, "impact": failure["description"], "severity": "HIGH"}]
        for entity_id in downstream:
            if random.random() < cascade_prob:
                blast_radius.append({
                    "entity": entity_id,
                    "impact": f"cascade from {target}",
                    "severity": "MEDIUM",
                })

        resilience_gaps = []
        if len(downstream) > 3 and cascade_prob > 0.5:
            resilience_gaps.append("No circuit breaker — cascade affects all downstream")
        if duration > 300:
            resilience_gaps.append("Recovery time exceeds SLA budget")

        recovery_path = [f"Restart {target}", "Verify health check passes"]
        if upstream:
            recovery_path.append(f"Verify {upstream[0]} connectivity")

        downtime = duration / 60 + random.uniform(0.5, 3)

        return {
            "blast_radius": blast_radius,
            "resilience_gaps": resilience_gaps,
            "recovery_path": recovery_path,
            "estimated_downtime_minutes": round(downtime, 1),
        }

    def _mock_chaos(
        self, target: str, failure: dict, duration: int,
        downstream: list[str], upstream: list[str],
    ) -> dict[str, Any]:
        """Mock chaos simulation."""
        blast = [{"entity": target, "impact": failure["description"], "severity": "HIGH"}]
        if downstream:
            blast.append({"entity": downstream[0], "impact": "cascade", "severity": "MEDIUM"})
        return {
            "blast_radius": blast,
            "resilience_gaps": ["mock simulation — SimPy not installed"],
            "recovery_path": [f"Restart {target}"],
            "estimated_downtime_minutes": round(duration / 60, 1),
        }
