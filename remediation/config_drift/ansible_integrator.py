"""
OmniWatch 2.0 — Config Drift Engine
Component: Ansible Integrator
Layer: 7 (Cross-Cutting)
Phase: 3
Purpose: Routes OS drift → Ansible EDA playbook execution
Inputs: ConfigDriftEvent (drift_source=os)
Outputs: Ansible playbook execution via subprocess
Technology: Python + subprocess (ansible-playbook CLI)
"""

import json
import logging
import subprocess
from typing import Any

from config import config
from remediation.config_drift import sanitize_config_value, sanitize_entity

logger = logging.getLogger(__name__)


class AnsibleIntegrator:
    """Triggers Ansible playbooks for OS configuration drift."""

    def __init__(self, playbook_dir: str = "remediation/policies/ansible"):
        self.playbook_dir = playbook_dir

    async def trigger_playbook(
        self, drift_event: dict[str, Any],
    ) -> dict[str, Any]:
        """Trigger Ansible playbook for OS drift.

        Args:
            drift_event: ConfigDriftEvent with drift_source="os".

        Returns:
            Dict with success status and execution details.
        """
        entity = sanitize_entity(drift_event.get("drifted_entity", ""))
        expected = sanitize_config_value(json.dumps(drift_event.get("expected_state", {})))
        actual = sanitize_config_value(json.dumps(drift_event.get("actual_state", {})))

        try:
            cmd = [
                "ansible-playbook",
                f"{self.playbook_dir}/os_drift_remediation.yml",
                "-e", f"drifted_entity={entity}",
                "-e", f"expected_config={expected}",
                "-e", f"actual_config={actual}",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=config.ANSIBLE_TIMEOUT)
            if proc.returncode == 0:
                return {"success": True, "output": proc.stdout.strip()[-500:]}
            return {"success": False, "output": proc.stderr.strip()[-500:]}
        except FileNotFoundError:
            return {"success": False, "output": "ansible-playbook not found", "error": "ansible binary not available"}
        except Exception as e:
            return {"success": False, "output": str(e)}
