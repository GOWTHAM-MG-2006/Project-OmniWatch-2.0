"""
OmniWatch 2.0 — SentinelPlane
Component: CSPMChecker
Layer: 9
Phase: 2
Purpose: Check cloud and Kubernetes security posture against CIS benchmarks
Inputs: K8s/cloud configuration paths
Outputs: Compliance check results with score → NexusStore
"""

import hashlib
import json
import logging
import subprocess
from datetime import datetime, timezone
from typing import Any

from config import config

logger = logging.getLogger(__name__)

CIS_CHECKS = {
    "CIS-K8s-1.1": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the API server audit log path is set",
        "severity": "MEDIUM",
    },
    "CIS-K8s-1.2": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the API server audit log maximum age is set",
        "severity": "MEDIUM",
    },
    "CIS-K8s-1.3": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the API server audit log maximum backup is set",
        "severity": "MEDIUM",
    },
    "CIS-K8s-1.4": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the API server request timeout is set",
        "severity": "HIGH",
    },
    "CIS-K8s-1.5": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the API server service account lookup is enabled",
        "severity": "HIGH",
    },
    "CIS-K8s-2.1": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the --anonymous-auth argument is set to false",
        "severity": "CRITICAL",
    },
    "CIS-K8s-2.2": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the --basic-auth-file argument is not set",
        "severity": "CRITICAL",
    },
    "CIS-K8s-2.3": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the --token-auth-file argument is not set",
        "severity": "CRITICAL",
    },
    "CIS-K8s-2.4": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the --kubelet-client-certificate argument is set",
        "severity": "HIGH",
    },
    "CIS-K8s-2.5": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the --kubelet-client-key argument is set",
        "severity": "HIGH",
    },
    "CIS-K8s-4.1": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the kubelet certificate authority is set",
        "severity": "HIGH",
    },
    "CIS-K8s-4.2": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the kubelet client certificate is set",
        "severity": "HIGH",
    },
    "CIS-K8s-5.1": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that the CNI plugin supports network policies",
        "severity": "HIGH",
    },
    "CIS-K8s-5.2": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "Ensure that all Namespaces have Network Policies defined",
        "severity": "HIGH",
    },
    "CIS-K8s-5.7": {
        "benchmark": "CIS Kubernetes Benchmark v1.8",
        "description": "The default namespace should not be used",
        "severity": "MEDIUM",
    },
}

SEVERITY_SCORES = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "INFO": 4,
}


class CSPMChecker:
    def __init__(self):
        self.checkov_available = self._check_checkov()

    def _check_checkov(self) -> bool:
        try:
            subprocess.run(
                ["checkov", "--version"],
                capture_output=True,
                timeout=config.SCANNER_TIMEOUT,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False

    def check_config(self, config_path: str) -> dict[str, Any]:
        if self.checkov_available:
            return self._check_with_checkov(config_path)
        return self._mock_check(config_path)

    def _check_with_checkov(self, config_path: str) -> dict[str, Any]:
        try:
            cmd = ["checkov", "-d", config_path, "-o", "json", "--framework", "kubernetes"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=config.SCANNER_SCAN_TIMEOUT)
            if result.returncode not in (0, 1):
                return self._mock_check(config_path)

            data = json.loads(result.stdout)
            checks = []
            for check_id, check_data in data.items():
                for result_item in check_data.get("results", []):
                    checks.append({
                        "check_id": check_id,
                        "name": result_item.get("check", {}).get("name", check_id),
                        "passed": result_item.get("result") == "passed",
                        "severity": result_item.get("check", {}).get("severity", "MEDIUM"),
                        "resource": result_item.get("resource", ""),
                        "file_path": result_item.get("file_path", ""),
                    })

            return self._build_result(config_path, checks)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            logger.warning("Checkov scan failed for %s: %s", config_path, e)
            return {"config_path": config_path, "checks": [], "total": 0, "passed": 0, "failed": 0, "error": str(e)}

    def _mock_check(self, config_path: str) -> dict[str, Any]:
        """Fallback when checkov is not available."""
        return {"config_path": config_path, "checks": [], "total": 0, "passed": 0, "failed": 0, "error": "checkov not installed"}

    def _build_result(self, config_path: str, checks: list[dict]) -> dict[str, Any]:
        total = len(checks)
        passed = sum(1 for c in checks if c["passed"])
        failed = total - passed
        score = round((passed / total * 100), 1) if total > 0 else 0.0

        failed_checks = [c for c in checks if not c["passed"]]
        severity_breakdown: dict[str, int] = {}
        for c in failed_checks:
            sev = c.get("severity", "MEDIUM")
            severity_breakdown[sev] = severity_breakdown.get(sev, 0) + 1

        return {
            "config_path": config_path,
            "check_time": datetime.now(timezone.utc).isoformat(),
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "compliance_score": score,
            "failed_checks": failed_checks,
            "severity_breakdown": severity_breakdown,
            "scanner": "checkov" if self.checkov_available else "mock",
        }

    def get_compliance_summary(self, check_results: list[dict[str, Any]]) -> dict[str, Any]:
        total_checks = 0
        total_passed = 0
        total_failed = 0
        all_severity_breakdown: dict[str, int] = {}

        for result in check_results:
            total_checks += result.get("total_checks", 0)
            total_passed += result.get("passed", 0)
            total_failed += result.get("failed", 0)
            for sev, count in result.get("severity_breakdown", {}).items():
                all_severity_breakdown[sev] = all_severity_breakdown.get(sev, 0) + count

        overall_score = round((total_passed / total_checks * 100), 1) if total_checks > 0 else 0.0

        frameworks = {}
        for result in check_results:
            for c in result.get("failed_checks", []):
                check_id = c.get("check_id", "")
                prefix = check_id.split("-")[0] if "-" in check_id else "UNKNOWN"
                if prefix not in frameworks:
                    frameworks[prefix] = {"passed": 0, "failed": 0}
                frameworks[prefix]["failed"] += 1

        return {
            "summary_time": datetime.now(timezone.utc).isoformat(),
            "total_checks": total_checks,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_compliance_score": overall_score,
            "severity_breakdown": all_severity_breakdown,
            "frameworks": frameworks,
            "num_scans": len(check_results),
        }
