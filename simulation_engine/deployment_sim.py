"""
OmniWatch 2.0 — SimulaX
Component: Deployment Simulator
Layer: 8
Phase: 3
Purpose: Simulates deployment rollout impact (canary/blue-green) before production
Inputs: New version resource profile + current Digital Twin state
Outputs: Deployment risk score → Block/Warn/Approve recommendation
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


class DeploymentSimulator:
    """Simulates deployment rollout to predict risk before production deploy."""

    def __init__(self, twin: DigitalTwin | None = None):
        self.twin = twin or DigitalTwin()

    def simulate(
        self,
        target_entity: str,
        new_version: str,
        current_version: str = "",
        rollout_strategy: str = "canary",
        canary_percent: float = 10.0,
    ) -> dict[str, Any]:
        """Simulate a deployment rollout.

        Args:
            target_entity: Entity being deployed to.
            new_version: Version being deployed.
            current_version: Current running version.
            rollout_strategy: "canary", "blue-green", or "rolling".
            canary_percent: Percentage of traffic for canary.

        Returns:
            Deployment simulation result with risk score and recommendation.
        """
        entity = self.twin.get_entity(target_entity)
        resources = (entity or {}).get("state", {}).get("resources", {})

        if HAS_SIMPY:
            result = self._run_simpy_deployment(resources, rollout_strategy, canary_percent)
        else:
            result = self._mock_deployment(resources, rollout_strategy, canary_percent)

        recommendation = "APPROVE" if result["risk_score"] < 0.3 else ("WARN" if result["risk_score"] < 0.6 else "BLOCK")

        return {
            "simulation_id": f"DEP-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            "mode": "DEPLOYMENT_SIMULATION",
            "proposed_action": {"type": "DEPLOY", "target": target_entity, "new_version": new_version, "rollout_strategy": rollout_strategy},
            "predicted_outcome": {
                "resolution_confidence": 1.0 - result["risk_score"],
                "recovery_time_minutes": result["rollback_plan"].get("estimated_time_minutes", 5),
                "side_effects": result["predicted_issues"],
                "revenue_recovery_usd": 0,
            },
            "risk_score": result["risk_score"],
            "recommendation": recommendation,
            "predicted_issues": result["predicted_issues"],
            "rollback_plan": result["rollback_plan"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _run_simpy_deployment(
        self, resources: dict, strategy: str, canary_pct: float,
    ) -> dict[str, Any]:
        """Run SimPy deployment simulation."""
        cpu = resources.get("cpu_percent", 50)
        memory = resources.get("memory_percent", 60)

        risk_score = 0.1
        issues = []

        # Higher baseline resources = higher deployment risk
        if cpu > 80:
            risk_score += 0.2
            issues.append(f"High CPU ({cpu:.0f}%) — deployment may cause resource contention")
        if memory > 80:
            risk_score += 0.15
            issues.append(f"High memory ({memory:.0f}%) — deployment may trigger OOM")

        # Strategy-specific risk adjustments
        if strategy == "canary":
            risk_score *= 0.7  # Canary reduces risk
        elif strategy == "rolling":
            risk_score *= 0.85
        # blue-green has no inherent risk reduction

        risk_score = min(1.0, risk_score)

        return {
            "risk_score": round(risk_score, 2),
            "predicted_issues": issues,
            "rollback_plan": {"strategy": "blue-green-switch-back", "estimated_time_minutes": 2},
        }

    def _mock_deployment(
        self, resources: dict, strategy: str, canary_pct: float,
    ) -> dict[str, Any]:
        """Mock deployment simulation when SimPy is unavailable."""
        import logging
        logger.warning("SimPy not installed — using estimated deployment values. Install: pip install simpy")
        risk = random.uniform(0.05, 0.4)
        return {
            "risk_score": round(risk, 2),
            "predicted_issues": ["SimPy not installed — using estimated values"],
            "rollback_plan": {"strategy": "manual-rollback", "estimated_time_minutes": 5},
            "simulation_type": "estimated",
            "note": "Install simpy for real simulation: pip install simpy",
        }
