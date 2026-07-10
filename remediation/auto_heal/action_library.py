"""
OmniWatch 2.0 — AutoHeal
Component: Action Library
Layer: 7
Phase: 3
Purpose: Predefined remediation actions library with parameters
Inputs: Action type (restart_pod, rollback, scale, rotate_credentials, etc.)
Outputs: Action parameters dict for remediation_engine
Technology: Python
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Action type definitions with required parameters
ACTION_DEFINITIONS = {
    "restart_pod": {
        "description": "Restart a Kubernetes pod",
        "required_params": ["namespace", "pod_name"],
        "optional_params": ["grace_period_seconds"],
        "k8s_verb": "delete",
        "risk_level": "low",
    },
    "rollback": {
        "description": "Rollback deployment to previous version",
        "required_params": ["namespace", "deployment_name", "to_revision"],
        "optional_params": [],
        "k8s_verb": "rollout_undo",
        "risk_level": "medium",
    },
    "scale": {
        "description": "Scale deployment replicas",
        "required_params": ["namespace", "deployment_name", "replicas"],
        "optional_params": [],
        "k8s_verb": "scale",
        "risk_level": "low",
    },
    "rotate_credentials": {
        "description": "Rotate secrets/credentials for a service",
        "required_params": ["namespace", "secret_name"],
        "optional_params": ["new_password"],
        "k8s_verb": "replace_secret",
        "risk_level": "medium",
    },
    "circuit_breaker": {
        "description": "Enable circuit breaker for a service",
        "required_params": ["service_name", "namespace"],
        "optional_params": ["failure_threshold", "timeout_seconds"],
        "k8s_verb": "patch",
        "risk_level": "low",
    },
    "block_ip": {
        "description": "Block an IP address at network level",
        "required_params": ["ip_address"],
        "optional_params": ["duration_seconds"],
        "k8s_verb": "network_policy",
        "risk_level": "low",
    },
    "config_drift_fix": {
        "description": "Fix configuration drift via ArgoCD/Ansible/Terraform",
        "required_params": ["drift_source", "drifted_entity"],
        "optional_params": ["remediation_tool"],
        "k8s_verb": "external",
        "risk_level": "medium",
    },
}


class ActionLibrary:
    """Provides predefined remediation action templates."""

    def get_action(self, action_type: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get action parameters for a given action type.

        Args:
            action_type: One of the ACTION_DEFINITIONS keys.
            overrides: Override default parameters.

        Returns:
            Action parameters dict ready for remediation_engine.
        """
        definition = ACTION_DEFINITIONS.get(action_type)
        if definition is None:
            raise ValueError(f"Unknown action type: {action_type}. Available: {list(ACTION_DEFINITIONS.keys())}")

        params = {
            "action_type": action_type,
            "description": definition["description"],
            "risk_level": definition["risk_level"],
            "k8s_verb": definition["k8s_verb"],
            "parameters": {},
        }

        # Set required params from overrides or defaults
        for param in definition["required_params"]:
            if overrides and param in overrides:
                params["parameters"][param] = overrides[param]
            else:
                params["parameters"][param] = None  # Must be provided

        # Set optional params
        for param in definition.get("optional_params", []):
            if overrides and param in overrides:
                params["parameters"][param] = overrides[param]

        return params

    def validate_action(self, action: dict[str, Any]) -> list[str]:
        """Validate that an action has all required parameters.

        Returns:
            List of missing parameter names (empty if valid).
        """
        action_type = action.get("action_type", "")
        definition = ACTION_DEFINITIONS.get(action_type)
        if definition is None:
            return [f"Unknown action type: {action_type}"]

        missing = []
        params = action.get("parameters", {})
        for param in definition["required_params"]:
            if param not in params or params[param] is None:
                missing.append(param)

        return missing

    def list_actions(self) -> list[dict[str, str]]:
        """List all available action types."""
        return [
            {"type": k, "description": v["description"], "risk_level": v["risk_level"]}
            for k, v in ACTION_DEFINITIONS.items()
        ]
