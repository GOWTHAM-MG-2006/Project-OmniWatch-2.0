"""
OmniWatch 2.0 — Config Drift Engine
Component: Git Integrator
Layer: 7 (Cross-Cutting)
Phase: 3
Purpose: Routes Git drift → Auto-revert commit
Inputs: ConfigDriftEvent (drift_source=git)
Outputs: Git revert command execution
Technology: Python + gitpython
"""

import logging
import subprocess
from typing import Any

from remediation.config_drift import sanitize_commit, sanitize_entity

logger = logging.getLogger(__name__)


class GitIntegrator:
    """Auto-reverts bad Git commits when drift is detected."""

    def __init__(self):
        pass

    async def trigger_revert(
        self, drift_event: dict[str, Any],
    ) -> dict[str, Any]:
        """Trigger Git revert for drift.

        Args:
            drift_event: ConfigDriftEvent with drift_source="git".

        Returns:
            Dict with success status and revert details.
        """
        entity = sanitize_entity(drift_event.get("drifted_entity", ""))
        actual_state = drift_event.get("actual_state", {})
        commit = sanitize_commit(actual_state.get("commit", ""))

        try:
            import git
            repo = git.Repo(entity)
            if commit:
                repo.git.revert(commit, no_edit=True)
                logger.info("Reverted commit %s in %s", commit[:8], entity)
                return {"success": True, "output": f"Reverted commit {commit[:8]} in {entity}"}
            # Revert last commit
            repo.git.revert("HEAD", no_edit=True)
            return {"success": True, "output": f"Reverted last commit in {entity}"}
        except ImportError:
            return {"success": False, "output": "gitpython not installed", "error": "gitpython dependency missing"}
        except Exception as e:
            return {"success": False, "output": str(e)}
