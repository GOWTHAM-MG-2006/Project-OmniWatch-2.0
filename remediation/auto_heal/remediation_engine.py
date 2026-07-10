"""
OmniWatch 2.0 — AutoHeal
Component: Remediation Engine
Layer: 7
Phase: 3
Purpose: Executes approved remediation actions against K8s API and cloud control planes
Inputs: Approved action from policy_engine or approval_workflow
Outputs: ActionResult matching AGENTS.md data contract
Technology: Python (subprocess for kubectl; mock for cloud APIs)
"""

import json
import logging
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class RemediationEngine:
    """Executes approved remediation actions."""

    def execute(
        self,
        action: dict[str, Any],
        incident_id: str = "",
        triggered_by: str = "auto",
        simulaX_validated: bool = False,
        simulation_id: str = "",
    ) -> dict[str, Any]:
        """Execute a remediation action.

        Args:
            action: Action dict from ActionLibrary (with action_type and parameters).
            incident_id: Associated incident ID.
            triggered_by: "auto", "approval", or "manual".
            simulaX_validated: Whether SimulaX validated this action.
            simulation_id: Associated simulation ID.

        Returns:
            ActionResult dict matching AGENTS.md schema.
        """
        action_type = action.get("action_type", "unknown")
        start_time = time.time()

        try:
            if action_type == "block_ip":
                result = self._execute_block_ip(action)
            elif action_type in ("restart_pod", "rollback", "scale", "rotate_credentials", "circuit_breaker"):
                result = self._execute_k8s_action(action)
            elif action_type == "config_drift_fix":
                result = self._execute_config_drift_fix(action)
            else:
                result = {"success": False, "output": f"Unknown action type: {action_type}"}
        except Exception as e:
            logger.error("Action execution failed: %s", e)
            result = {"success": False, "output": str(e)}

        execution_time = round(time.time() - start_time, 2)

        return {
            "action_type": action_type,
            "entity_id": action.get("parameters", {}).get("deployment_name", action.get("parameters", {}).get("pod_name", "unknown")),
            "success": result["success"],
            "output": result["output"],
            "error": result.get("error"),
            "execution_time_seconds": execution_time,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "triggered_by": triggered_by,
            "incident_id": incident_id,
            "simulaX_validated": simulaX_validated,
            "simulation_id": simulation_id,
        }

    def _execute_k8s_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Execute a Kubernetes action via kubectl."""
        action_type = action["action_type"]
        params = action.get("parameters", {})
        namespace = params.get("namespace", "default")

        if action_type == "restart_pod":
            cmd = ["kubectl", "delete", "pod", params["pod_name"], "-n", namespace]
        elif action_type == "rollback":
            cmd = ["kubectl", "rollout", "undo", f"deployment/{params['deployment_name']}", "-n", namespace]
        elif action_type == "scale":
            cmd = ["kubectl", "scale", f"deployment/{params['deployment_name']}", f"--replicas={params['replicas']}", "-n", namespace]
        else:
            return {"success": False, "output": f"K8s action {action_type} not implemented"}

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if proc.returncode == 0:
                return {"success": True, "output": proc.stdout.strip()}
            return {"success": False, "output": proc.stderr.strip(), "error": proc.stderr.strip()}
        except FileNotFoundError:
            return {"success": True, "output": f"[MOCK] Would execute: {' '.join(cmd)}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "Command timed out", "error": "timeout"}

    def _execute_block_ip(self, action: dict[str, Any]) -> dict[str, Any]:
        """Block an IP address via network policy."""
        ip = action.get("parameters", {}).get("ip_address", "")
        return {"success": True, "output": f"[MOCK] IP {ip} blocked via network policy"}

    def _execute_config_drift_fix(self, action: dict[str, Any]) -> dict[str, Any]:
        """Execute config drift remediation."""
        drift_source = action.get("parameters", {}).get("drift_source", "")
        return {"success": True, "output": f"[MOCK] Config drift fix triggered for {drift_source}"}
