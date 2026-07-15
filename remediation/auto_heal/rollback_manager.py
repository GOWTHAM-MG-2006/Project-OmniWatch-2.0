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

from config import config

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
        """Execute a rollback plan via kubectl or API.

        Returns:
            ActionResult dict.
        """
        import subprocess
        import time

        rollback_action = rollback_plan.get("rollback_action", {})
        action_type = rollback_action.get("action_type", "rollback")
        params = rollback_action.get("parameters", {})
        deployment_name = params.get("deployment_name", "unknown")
        namespace = params.get("namespace", "default")
        to_revision = params.get("to_revision", "")

        start_time = time.time()
        success = False
        output = ""
        error_msg = None

        try:
            if action_type == "rollback":
                cmd = ["kubectl", "rollout", "undo", f"deployment/{deployment_name}",
                       "-n", namespace]
                if to_revision:
                    cmd.append(f"--to-revision={to_revision}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=config.K8S_ACTION_TIMEOUT)
                success = result.returncode == 0
                output = result.stdout if success else result.stderr
                error_msg = None if success else result.stderr
            elif action_type == "scale":
                replicas = params.get("replicas", 1)
                cmd = ["kubectl", "scale", f"deployment/{deployment_name}",
                       f"--replicas={replicas}", "-n", namespace]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=config.K8S_ACTION_TIMEOUT)
                success = result.returncode == 0
                output = result.stdout if success else result.stderr
                error_msg = None if success else result.stderr
            elif action_type == "restart":
                cmd = ["kubectl", "rollout", "restart", f"deployment/{deployment_name}",
                       "-n", namespace]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=config.K8S_ACTION_TIMEOUT)
                success = result.returncode == 0
                output = result.stdout if success else result.stderr
                error_msg = None if success else result.stderr
            else:
                error_msg = f"Unsupported rollback action type: {action_type}"
                output = error_msg

        except FileNotFoundError:
            error_msg = "kubectl not found — install kubectl or run in Kubernetes environment"
            output = error_msg
        except subprocess.TimeoutExpired:
            error_msg = "Rollback timed out after 300 seconds"
            output = error_msg
        except Exception as e:
            error_msg = str(e)
            output = error_msg

        duration = round(time.time() - start_time, 2)

        return {
            "action_type": action_type,
            "entity_id": deployment_name,
            "success": success,
            "output": output[:500] if output else "",
            "error": error_msg,
            "execution_time_seconds": duration,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "triggered_by": "rollback",
            "incident_id": rollback_plan.get("incident_id", ""),
            "simulaX_validated": rollback_plan.get("simulaX_validated", False),
            "simulation_id": rollback_plan.get("simulation_id", ""),
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
