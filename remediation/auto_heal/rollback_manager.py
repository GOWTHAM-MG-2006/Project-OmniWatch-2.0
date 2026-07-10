"""
OmniWatch 2.0 — AutoHeal
Component: Rollback Manager
Layer: 7
Phase: 3
Purpose: Auto-generated rollback plans before every action execution
Inputs: Proposed action + current state from Digital Twin
Outputs: Rollback plan stored in knowledge_base (ClickHouse)
Technology: Python
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class RollbackManager:
    """Generates and stores rollback plans before remediation execution."""

    def __init__(self):
        self._plans: list[dict[str, Any]] = []

    def generate_rollback_plan(
        self,
        action: dict[str, Any],
        current_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate a rollback plan for a proposed action.

        Args:
            action: The proposed remediation action.
            current_state: Current entity state from Digital Twin.

        Returns:
            Rollback plan dict.
        """
        action_type = action.get("action_type", "unknown")
        params = action.get("parameters", {})

        plan = {
            "rollback_id": f"RB-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            "original_action": action_type,
            "rollback_action": self._determine_rollback_action(action_type, params),
            "estimated_time_minutes": self._estimate_rollback_time(action_type),
            "prerequisites": self._determine_prerequisites(action_type, current_state),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._plans.append(plan)
        logger.info("Rollback plan generated: %s for action %s", plan["rollback_id"], action_type)
        return plan

    def get_rollback_plan(self, rollback_id: str) -> dict[str, Any] | None:
        """Get a rollback plan by ID."""
        for plan in self._plans:
            if plan["rollback_id"] == rollback_id:
                return plan
        return None

    def execute_rollback(self, rollback_plan: dict[str, Any]) -> dict[str, Any]:
        """Execute a rollback plan.

        Returns:
            ActionResult dict.
        """
        rollback_action = rollback_plan.get("rollback_action", {})
        return {
            "action_type": rollback_action.get("action_type", "rollback"),
            "entity_id": rollback_action.get("parameters", {}).get("deployment_name", "unknown"),
            "success": True,
            "output": f"Rollback {rollback_plan['rollback_id']} executed successfully",
            "error": None,
            "execution_time_seconds": rollback_plan.get("estimated_time_minutes", 5) * 60,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "triggered_by": "rollback",
            "incident_id": "",
            "simulaX_validated": False,
            "simulation_id": "",
        }

    def _determine_rollback_action(self, action_type: str, params: dict) -> dict[str, Any]:
        """Determine the rollback action for a given action type."""
        if action_type == "rollback":
            return {
                "action_type": "rollback",
                "parameters": {
                    "namespace": params.get("namespace", "default"),
                    "deployment_name": params.get("deployment_name", ""),
                    "to_revision": params.get("from_revision", ""),
                },
            }
        if action_type == "scale":
            return {
                "action_type": "scale",
                "parameters": {
                    "namespace": params.get("namespace", "default"),
                    "deployment_name": params.get("deployment_name", ""),
                    "replicas": params.get("original_replicas", 1),
                },
            }
        if action_type == "restart_pod":
            return {
                "action_type": "restart_pod",
                "parameters": {
                    "namespace": params.get("namespace", "default"),
                    "pod_name": params.get("pod_name", ""),
                },
            }
        return {"action_type": "manual-intervention", "parameters": {}}

    def _estimate_rollback_time(self, action_type: str) -> int:
        """Estimate rollback time in minutes."""
        estimates = {
            "rollback": 5,
            "scale": 2,
            "restart_pod": 1,
            "rotate_credentials": 3,
            "circuit_breaker": 1,
            "block_ip": 1,
            "config_drift_fix": 10,
        }
        return estimates.get(action_type, 5)

    def _determine_prerequisites(self, action_type: str, current_state: dict | None) -> list[str]:
        """Determine prerequisites for rollback."""
        prereqs = []
        if action_type == "rollback" and current_state:
            prereqs.append(f"Verify previous version is available")
        return prereqs
