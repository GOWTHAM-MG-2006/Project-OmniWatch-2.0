"""
OmniWatch 2.0 — Config Drift Engine
Component: Terraform Integrator
Layer: 7 (Cross-Cutting)
Phase: 3
Purpose: Routes cloud drift → Terraform state reconciliation
Inputs: ConfigDriftEvent (drift_source=cloud)
Outputs: Terraform plan + apply results
Technology: Python + subprocess (terraform CLI)
"""

import logging
import subprocess
from typing import Any

from config import config
from remediation.config_drift import sanitize_entity

logger = logging.getLogger(__name__)


class TerraformIntegrator:
    """Executes Terraform state reconciliation for cloud drift."""

    def __init__(self, terraform_dir: str = "infrastructure/terraform"):
        self.terraform_dir = terraform_dir

    async def trigger_reconciliation(
        self, drift_event: dict[str, Any],
    ) -> dict[str, Any]:
        """Trigger Terraform state reconciliation.

        Args:
            drift_event: ConfigDriftEvent with drift_source="cloud".

        Returns:
            Dict with success status and apply details.
        """
        entity = sanitize_entity(drift_event.get("drifted_entity", ""))

        try:
            # Plan first
            plan_cmd = ["terraform", "plan", "-out=tfplan", "-no-color"]
            plan_proc = subprocess.run(plan_cmd, capture_output=True, text=True, timeout=config.TERRAFORM_TIMEOUT, cwd=self.terraform_dir)

            if plan_proc.returncode == 0:
                # No changes needed
                return {"success": True, "output": "No Terraform changes required"}

            if plan_proc.returncode == 2:
                # Changes detected — apply
                apply_cmd = ["terraform", "apply", "-auto-approve", "tfplan", "-no-color"]
                apply_proc = subprocess.run(apply_cmd, capture_output=True, text=True, timeout=config.TERRAFORM_APPLY_TIMEOUT, cwd=self.terraform_dir)
                if apply_proc.returncode == 0:
                    return {"success": True, "output": f"Terraform apply completed for {entity}"}
                return {"success": False, "output": apply_proc.stderr.strip()[-500:]}

            return {"success": False, "output": plan_proc.stderr.strip()[-500:]}
        except FileNotFoundError:
            return {"success": False, "output": "terraform not found", "error": "terraform binary not available"}
        except Exception as e:
            return {"success": False, "output": str(e)}
