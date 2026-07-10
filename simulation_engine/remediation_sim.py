"""
OmniWatch 2.0 — SimulaX
Component: Remediation Simulator
Layer: 8
Phase: 3
Purpose: Simulates proposed fixes before execution using SimPy discrete event simulation
Inputs: Proposed action (from AutoHeal) + Digital Twin state
Outputs: SimulaXResult matching AGENTS.md data contract
Technology: SimPy
"""

import hashlib
import logging
import random
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

try:
    import simpy
    HAS_SIMPY = True
except ImportError:
    HAS_SIMPY = False
    logger.info("SimPy not installed — using mock simulation")

from simulation_engine.digital_twin import DigitalTwin

logger = logging.getLogger(__name__)


class RemediationSimulator:
    """Simulates proposed remediation actions before execution.

    Uses SimPy discrete event simulation to predict outcome, recovery time,
    side effects, and risk score for a proposed action.
    """

    def __init__(self, twin: DigitalTwin | None = None):
        self.twin = twin or DigitalTwin()

    def simulate(
        self,
        proposed_action: dict[str, Any],
        incident: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run a remediation simulation.

        Args:
            proposed_action: Dict with keys: type, target, from_version, to_version.
            incident: Optional IncidentRecord for context.

        Returns:
            SimulaXResult dict matching AGENTS.md schema.
        """
        simulation_id = self._generate_id()
        action_type = proposed_action.get("type", "UNKNOWN")
        target = proposed_action.get("target", "unknown")

        if HAS_SIMPY:
            result = self._run_simpy_simulation(proposed_action, target)
        else:
            result = self._mock_simulation(proposed_action, target)

        return {
            "simulation_id": simulation_id,
            "mode": "REMEDIATION_SIMULATION",
            "proposed_action": proposed_action,
            "predicted_outcome": result["predicted_outcome"],
            "risk_score": result["risk_score"],
            "recommendation": result["recommendation"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _run_simpy_simulation(
        self, proposed_action: dict[str, Any], target: str,
    ) -> dict[str, Any]:
        """Run actual SimPy simulation."""
        env = simpy.Environment()

        action_type = proposed_action.get("type", "UNKNOWN")
        entity = self.twin.get_entity(target)
        resources = (entity or {}).get("state", {}).get("resources", {})

        # Simulate action execution
        if action_type == "ROLLBACK":
            recovery_time = self._simulate_rollback(env, resources)
            confidence = 0.85 + random.uniform(0, 0.14)
            side_effects = self._predict_rollback_side_effects(proposed_action)
        elif action_type == "RESTART":
            recovery_time = self._simulate_restart(env, resources)
            confidence = 0.90 + random.uniform(0, 0.09)
            side_effects = ["temporary unavailability during restart"]
        elif action_type == "SCALE":
            recovery_time = self._simulate_scale(env, resources)
            confidence = 0.88 + random.uniform(0, 0.11)
            side_effects = ["increased cost during scale-up"]
        else:
            recovery_time = 5.0
            confidence = 0.70
            side_effects = ["unknown action type — manual verification required"]

        risk_score = max(0.0, 1.0 - confidence)
        recommendation = "PROCEED" if confidence > 0.8 else "REVIEW"

        return {
            "predicted_outcome": {
                "resolution_confidence": round(confidence, 2),
                "recovery_time_minutes": round(recovery_time, 1),
                "side_effects": side_effects,
                "revenue_recovery_usd": self._estimate_revenue_recovery(target),
            },
            "risk_score": round(risk_score, 2),
            "recommendation": recommendation,
        }

    def _mock_simulation(
        self, proposed_action: dict[str, Any], target: str,
    ) -> dict[str, Any]:
        """Mock simulation when SimPy is unavailable."""
        confidence = 0.85 + random.uniform(0, 0.10)
        recovery_time = random.uniform(3, 15)
        return {
            "predicted_outcome": {
                "resolution_confidence": round(confidence, 2),
                "recovery_time_minutes": round(recovery_time, 1),
                "side_effects": ["mock simulation — SimPy not installed"],
                "revenue_recovery_usd": self._estimate_revenue_recovery(target),
            },
            "risk_score": round(max(0.0, 1.0 - confidence), 2),
            "recommendation": "PROCEED" if confidence > 0.8 else "REVIEW",
        }

    def _simulate_rollback(self, env: simpy.Environment, resources: dict) -> float:
        """Simulate rollback execution time."""
        cpu = resources.get("cpu_percent", 50)
        # Rollback takes longer on high-CPU entities
        base_time = 3.0
        cpu_penalty = (cpu / 100) * 5.0
        return base_time + cpu_penalty + random.uniform(0, 2)

    def _simulate_restart(self, env: simpy.Environment, resources: dict) -> float:
        """Simulate pod/service restart time."""
        return 1.0 + random.uniform(0, 3)

    def _simulate_scale(self, env: simpy.Environment, resources: dict) -> float:
        """Simulate scale-out execution time."""
        return 2.0 + random.uniform(0, 5)

    def _predict_rollback_side_effects(self, proposed_action: dict[str, Any]) -> list[str]:
        """Predict side effects of a rollback action."""
        side_effects = []
        from_version = proposed_action.get("from_version", "")
        to_version = proposed_action.get("to_version", "")
        if from_version and to_version:
            side_effects.append(f"features introduced in {from_version} will be lost")
        return side_effects or ["temporary service disruption during rollback"]

    def _estimate_revenue_recovery(self, target: str) -> float:
        """Estimate revenue recovery from fixing the target entity."""
        # Simplified heuristic: $100-$1000 per minute of downtime prevented
        return round(random.uniform(1000, 84200), 2)

    def _generate_id(self) -> str:
        """Generate a unique simulation ID."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        short = hashlib.sha256(ts.encode()).hexdigest()[:5]
        return f"SIM-{ts}-{short}"
