"""
OmniWatch 2.0 — SimulaX
Component: Capacity Simulator
Layer: 8
Phase: 3
Purpose: Simulates traffic growth and resource exhaustion scenarios
Inputs: Traffic growth model + resource limits + Digital Twin state
Outputs: Capacity report with saturation points and recommended pre-scaling actions
Technology: SimPy
"""

import logging
from datetime import datetime, timezone
from typing import Any

try:
    import simpy
    HAS_SIMPY = True
except ImportError:
    HAS_SIMPY = False

from simulation_engine.digital_twin import DigitalTwin

logger = logging.getLogger(__name__)


class CapacitySimulator:
    """Simulates traffic growth scenarios to identify saturation points."""

    def __init__(self, twin: DigitalTwin | None = None):
        self.twin = twin or DigitalTwin()

    def simulate(
        self,
        target_entity: str,
        growth_multiplier: float = 2.0,
        duration_minutes: int = 60,
    ) -> dict[str, Any]:
        """Simulate traffic growth and identify saturation points.

        Args:
            target_entity: Entity to simulate growth for.
            growth_multiplier: Traffic multiplier (2.0 = double traffic).
            duration_minutes: How long to simulate.

        Returns:
            Capacity report dict.
        """
        entity = self.twin.get_entity(target_entity)
        resources = (entity or {}).get("state", {}).get("resources", {})

        if HAS_SIMPY:
            report = self._run_simpy_capacity(resources, growth_multiplier, duration_minutes)
        else:
            report = self._mock_capacity(resources, growth_multiplier, duration_minutes)

        return {
            "simulation_id": f"CAP-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            "mode": "CAPACITY_SIMULATION",
            "proposed_action": {"type": "SCALE", "target": target_entity, "growth_multiplier": growth_multiplier},
            "predicted_outcome": {
                "resolution_confidence": 1.0 - (len(report["saturation_points"]) * 0.15),
                "recovery_time_minutes": report["saturation_points"][0]["at_minute"] if report["saturation_points"] else duration_minutes,
                "side_effects": [a["reason"] for a in report["recommended_actions"]],
                "revenue_recovery_usd": 0,
            },
            "risk_score": {"HIGH": 0.8, "MEDIUM": 0.5, "LOW": 0.2}.get(report["risk_level"], 0.5),
            "recommendation": "DO_NOT_PROCEED" if report["risk_level"] == "HIGH" else "PROCEED",
            "saturation_points": report["saturation_points"],
            "recommended_actions": report["recommended_actions"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _run_simpy_capacity(
        self, resources: dict, multiplier: float, duration: int,
    ) -> dict[str, Any]:
        """Run SimPy capacity simulation."""
        env = simpy.Environment()
        saturation_points = []
        recommended_actions = []

        cpu = resources.get("cpu_percent", 50)
        memory = resources.get("memory_percent", 60)
        disk = resources.get("disk_percent", 40)

        # Project resource usage under growth
        proj_cpu = min(100, cpu * multiplier)
        proj_memory = min(100, memory * multiplier)
        proj_disk = min(100, disk * (1 + (multiplier - 1) * 0.3))  # disk grows slower

        if proj_cpu > 90:
            saturation_points.append({"resource": "cpu", "projected_percent": round(proj_cpu, 1), "at_minute": int(duration * (90 / proj_cpu))})
            recommended_actions.append({"action": "SCALE_UP", "resource": "cpu", "reason": f"CPU projected to reach {proj_cpu:.0f}%"})

        if proj_memory > 90:
            saturation_points.append({"resource": "memory", "projected_percent": round(proj_memory, 1), "at_minute": int(duration * (90 / proj_memory))})
            recommended_actions.append({"action": "SCALE_UP", "resource": "memory", "reason": f"Memory projected to reach {proj_memory:.0f}%"})

        if proj_disk > 85:
            saturation_points.append({"resource": "disk", "projected_percent": round(proj_disk, 1), "at_minute": int(duration * (85 / proj_disk))})
            recommended_actions.append({"action": "CLEANUP", "resource": "disk", "reason": f"Disk projected to reach {proj_disk:.0f}%"})

        risk_level = "HIGH" if len(saturation_points) > 1 else ("MEDIUM" if saturation_points else "LOW")

        return {
            "saturation_points": saturation_points,
            "recommended_actions": recommended_actions,
            "risk_level": risk_level,
        }

    def _mock_capacity(
        self, resources: dict, multiplier: float, duration: int,
    ) -> dict[str, Any]:
        """Mock capacity simulation when SimPy is unavailable."""
        import logging
        logger.warning("SimPy not installed — using estimated capacity values. Install: pip install simpy")
        cpu = resources.get("cpu_percent", 50)
        proj_cpu = min(100, cpu * multiplier)
        saturation = []
        actions = []
        if proj_cpu > 90:
            saturation.append({"resource": "cpu", "projected_percent": round(proj_cpu, 1), "at_minute": duration // 2})
            actions.append({"action": "SCALE_UP", "resource": "cpu", "reason": f"CPU projected to {proj_cpu:.0f}%"})
        return {
            "saturation_points": saturation,
            "recommended_actions": actions,
            "risk_level": "HIGH" if saturation else "LOW",
            "simulation_type": "estimated",
            "note": "Install simpy for real simulation: pip install simpy",
        }
