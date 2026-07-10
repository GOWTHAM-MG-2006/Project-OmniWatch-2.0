"""
OmniWatch 2.0 — Config Drift Engine
Component: Drift Detector
Layer: 7 (Cross-Cutting)
Phase: 3
Purpose: Detects configuration drift across K8s, OS, Cloud, Git layers
Inputs: Git diffs, K8s Watch API, Terraform state diffs
Outputs: ConfigDriftEvent matching AGENTS.md data contract
Technology: Python (gitpython, kubernetes client, subprocess for terraform)
"""

import hashlib
import json
import logging
import subprocess
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class DriftDetector:
    """Detects configuration drift across multiple infrastructure layers."""

    def detect_git_drift(
        self, repo_path: str, expected_branch: str = "main",
    ) -> list[dict[str, Any]]:
        """Detect drift between current Git state and expected branch.

        Args:
            repo_path: Path to the Git repository.
            expected_branch: Branch to compare against.

        Returns:
            List of ConfigDriftEvent dicts.
        """
        drifts = []
        try:
            import git
            repo = git.Repo(repo_path)
            current = repo.active_branch.commit.hexsha
            expected = repo.commit(expected_branch).hexsha

            if current != expected:
                diff = repo.commit(expected_branch).diff(repo.active_branch.commit)
                drifted_files = [d.a_path for d in diff]
                drifts.append(self._build_event(
                    drift_source="git",
                    detection_method="branch_diff",
                    drifted_entity=repo_path,
                    expected_state={"branch": expected_branch, "commit": expected},
                    actual_state={"branch": str(repo.active_branch), "commit": current, "files_changed": drifted_files},
                    remediation_tool="git",
                    confidence=0.95,
                ))
        except ImportError:
            logger.warning("gitpython not installed — git drift detection disabled")
        except Exception as e:
            logger.error("Git drift detection failed: %s", e)

        return drifts

    def detect_k8s_drift(
        self, namespace: str = "default", kubeconfig: str | None = None,
    ) -> list[dict[str, Any]]:
        """Detect drift between declared and actual K8s state.

        Uses kubectl to compare deployment specs.

        Args:
            namespace: K8s namespace to check.
            kubeconfig: Path to kubeconfig file.

        Returns:
            List of ConfigDriftEvent dicts.
        """
        drifts = []
        try:
            cmd = ["kubectl", "get", "deployments", "-n", namespace, "-o", "json"]
            if kubeconfig:
                cmd.extend(["--kubeconfig", kubeconfig])
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if proc.returncode == 0:
                deployments = json.loads(proc.stdout)
                for deploy in deployments.get("items", []):
                    name = deploy["metadata"]["name"]
                    spec = deploy.get("spec", {})
                    status = deploy.get("status", {})
                    desired = spec.get("replicas", 1)
                    actual = status.get("replicas", 0)
                    if desired != actual:
                        drifts.append(self._build_event(
                            drift_source="kubernetes",
                            detection_method="kubectl_diff",
                            drifted_entity=f"{namespace}/{name}",
                            expected_state={"replicas": desired},
                            actual_state={"replicas": actual},
                            remediation_tool="argocd",
                            confidence=0.98,
                        ))
        except FileNotFoundError:
            logger.warning("kubectl not available — K8s drift detection disabled")
        except Exception as e:
            logger.error("K8s drift detection failed: %s", e)

        return drifts

    def detect_terraform_drift(
        self, terraform_dir: str,
    ) -> list[dict[str, Any]]:
        """Detect drift between Terraform state and actual infrastructure.

        Args:
            terraform_dir: Path to Terraform configuration directory.

        Returns:
            List of ConfigDriftEvent dicts.
        """
        drifts = []
        try:
            proc = subprocess.run(
                ["terraform", "plan", "-detailed-exitcode", "-no-color"],
                capture_output=True, text=True, timeout=120,
                cwd=terraform_dir,
            )
            # Exit code 2 = changes detected
            if proc.returncode == 2:
                drifts.append(self._build_event(
                    drift_source="cloud",
                    detection_method="terraform_plan",
                    drifted_entity=terraform_dir,
                    expected_state={"plan": "no_changes"},
                    actual_state={"plan": "changes_detected", "summary": proc.stdout[:500]},
                    remediation_tool="terraform",
                    confidence=0.92,
                ))
        except FileNotFoundError:
            logger.warning("terraform not available — cloud drift detection disabled")
        except Exception as e:
            logger.error("Terraform drift detection failed: %s", e)

        return drifts

    def _build_event(
        self,
        drift_source: str,
        detection_method: str,
        drifted_entity: str,
        expected_state: dict,
        actual_state: dict,
        remediation_tool: str,
        confidence: float,
    ) -> dict[str, Any]:
        """Build a ConfigDriftEvent dict."""
        drift_id = f"DRF-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{hashlib.sha256(drifted_entity.encode()).hexdigest()[:4]}"
        return {
            "drift_id": drift_id,
            "drift_source": drift_source,
            "detection_method": detection_method,
            "drifted_entity": drifted_entity,
            "expected_state": expected_state,
            "actual_state": actual_state,
            "remediation_tool": remediation_tool,
            "remediation_action": f"{remediation_tool}-self-heal",
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
