"""
OmniWatch 2.0 — AutoHeal
Component: Policy Engine
Layer: 7
Phase: 3
Purpose: OPA Rego policy evaluation for auto vs approval decisions
Inputs: RootCauseObject + confidence + severity
Outputs: Policy decision (auto-remediate / approve-required / reject)
Technology: Python + OPA REST API
"""

import os
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPA_BASE_URL = os.getenv("OPA_ENDPOINT", "http://localhost:8181")


class PolicyEngine:
    """Evaluates OPA Rego policies to decide remediation action."""

    def __init__(self, opa_url: str | None = None):
        self.opa_url = (opa_url or OPA_BASE_URL).rstrip("/")

    async def evaluate(
        self,
        incident: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Evaluate remediation policy against an incident.

        Args:
            incident: IncidentRecord dict.
            context: Additional context (e.g., simulaX_validated, attack_type).

        Returns:
            Dict with keys: decision, policy_path, reason.
        """
        input_data = {
            "severity": incident.get("severity", "P4"),
            "confidence": incident.get("confidence", 0),
            "source": context.get("source", "performance") if context else "performance",
            "attack_type": context.get("attack_type", "") if context else "",
            "action": context.get("action", "") if context else "",
            "simulaX_validated": context.get("simulaX_validated", False) if context else False,
        }

        try:
            result = await self._query_opa("omniwatch/remediation", input_data)
            if result.get("allow"):
                return {"decision": "auto-remediate", "policy_path": "omniwatch/remediation", "reason": "Policy allows auto-remediation"}
            if result.get("require_approval"):
                return {"decision": "approve-required", "policy_path": "omniwatch/remediation", "reason": "Policy requires human approval"}
            if result.get("block_auto"):
                return {"decision": "reject", "policy_path": "omniwatch/remediation", "reason": "Policy blocks auto-remediation"}
        except Exception as e:
            logger.warning("OPA evaluation failed (%s), using fallback logic", e)

        return self._fallback_evaluate(input_data)

    async def evaluate_security(
        self, security_event: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate security-specific policy."""
        input_data = {
            "severity": security_event.get("severity", "LOW"),
            "confidence": security_event.get("confidence", 0),
            "source": "security",
            "attack_type": security_event.get("attack_type", ""),
            "action": security_event.get("recommended_action", ""),
        }
        try:
            result = await self._query_opa("omniwatch/security", input_data)
            if result.get("allow"):
                return {"decision": "auto-remediate", "policy_path": "omniwatch/security", "reason": "Security policy allows"}
            if result.get("require_approval"):
                return {"decision": "approve-required", "policy_path": "omniwatch/security", "reason": "Security action requires approval"}
            if result.get("block_auto"):
                return {"decision": "reject", "policy_path": "omniwatch/security", "reason": "Security policy blocks"}
        except Exception as e:
            logger.warning("OPA security evaluation failed: %s", e)

        return self._fallback_evaluate(input_data)

    async def evaluate_config_drift(
        self, drift_event: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate config drift policy."""
        input_data = {
            "drift_source": drift_event.get("drift_source", ""),
            "confidence": drift_event.get("confidence", 0),
            "remediation_tool": drift_event.get("remediation_tool", ""),
        }
        try:
            result = await self._query_opa("omniwatch/config_drift", input_data)
            if result.get("allow"):
                return {"decision": "auto-remediate", "policy_path": "omniwatch/config_drift", "reason": "Drift policy allows"}
            if result.get("require_approval"):
                return {"decision": "approve-required", "policy_path": "omniwatch/config_drift", "reason": "Drift requires approval"}
            if result.get("block_auto"):
                return {"decision": "reject", "policy_path": "omniwatch/config_drift", "reason": "Drift policy blocks"}
        except Exception as e:
            logger.warning("OPA drift evaluation failed: %s", e)

        return self._fallback_evaluate(input_data)

    async def _query_opa(self, policy_path: str, input_data: dict) -> dict:
        """Query OPA REST API."""
        url = f"{self.opa_url}/v1/data/{policy_path}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json={"input": input_data})
            resp.raise_for_status()
            return resp.json().get("result", {})

    def _fallback_evaluate(self, input_data: dict) -> dict[str, Any]:
        """Fallback logic when OPA is unavailable."""
        severity = input_data.get("severity", "P4")
        confidence = input_data.get("confidence", 0)
        source = input_data.get("source", "performance")

        if source == "security" and input_data.get("attack_type") == "BRUTE_FORCE" and confidence > 0.9:
            return {"decision": "auto-remediate", "policy_path": "fallback", "reason": "Brute force with high confidence"}

        if severity == "P1" and confidence > 0.95:
            return {"decision": "auto-remediate", "policy_path": "fallback", "reason": "P1 with very high confidence"}
        if severity in ("P1", "P2") and confidence > 0.7:
            return {"decision": "approve-required", "policy_path": "fallback", "reason": "Medium confidence requires approval"}
        if severity in ("P3", "P4"):
            return {"decision": "reject", "policy_path": "fallback", "reason": "Low severity — no auto-remediation"}

        return {"decision": "approve-required", "policy_path": "fallback", "reason": "Default: requires approval"}
