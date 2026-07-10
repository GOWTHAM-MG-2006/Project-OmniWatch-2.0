"""OmniWatch 2.0 — NeuroEngine
Component: Causal Hypothesis Builder
Layer: 6
Phase: 2
Purpose: Convert differential analysis results into ranked causal hypotheses
Inputs: DiffAnalyzer results + entity context
Outputs: List of ranked causal hypothesis dicts"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Maps attribute names to investigation guidance
INVESTIGATION_GUIDES: dict[str, dict[str, Any]] = {
    "status": {
        "type": "log_analysis",
        "steps": [
            "Filter logs by over-represented status code",
            "Correlate with timestamp of failure onset",
            "Check upstream/downstream service logs",
        ],
    },
    "host": {
        "type": "infrastructure",
        "steps": [
            "Check host resource utilization (CPU, memory, disk)",
            "Verify host health via cloud provider API",
            "Compare with peer hosts in same cluster",
        ],
    },
    "region": {
        "type": "geographic",
        "steps": [
            "Check region-specific infrastructure health",
            "Verify CDN/routing configuration",
            "Compare metrics across regions",
        ],
    },
    "service": {
        "type": "service_health",
        "steps": [
            "Check service deployment status",
            "Review recent deployments or config changes",
            "Examine service resource consumption",
        ],
    },
    "endpoint": {
        "type": "api_analysis",
        "steps": [
            "Analyze endpoint latency distribution",
            "Check request payload patterns",
            "Review endpoint-specific error logs",
        ],
    },
    "error_type": {
        "type": "error_analysis",
        "steps": [
            "Group errors by stack trace",
            "Identify error origin in code path",
            "Check for correlated code deployments",
        ],
    },
    "container": {
        "type": "container_health",
        "steps": [
            "Check container restart history",
            "Review OOM kill events",
            "Verify container resource limits",
        ],
    },
    "default": {
        "type": "generic_investigation",
        "steps": [
            "Review metric trends for this attribute",
            "Correlate with other anomalous attributes",
            "Check recent change events",
        ],
    },
}


class CausalHypothesisBuilder:
    """Converts differential analysis results into ranked causal hypotheses.

    Each hypothesis links an over-represented attribute to a potential root cause
    with investigation steps and TopoBrain cross-links.
    """

    def build_hypotheses(
        self,
        diff_results: list[dict[str, Any]],
        entity_id: str,
    ) -> list[dict[str, Any]]:
        """Convert diff results into ranked causal hypotheses.

        Args:
            diff_results: Output from DiffAnalyzer.analyze().
            entity_id: The primary entity under investigation.

        Returns:
            List of hypothesis dicts ranked by confidence.
        """
        if not diff_results:
            return []

        hypotheses: list[dict[str, Any]] = []

        for i, diff in enumerate(diff_results):
            attribute = diff["attribute"]
            value = diff["over_represented_value"]
            score = diff["score"]

            description = self._generate_description(attribute, value, entity_id, diff)
            topo_links = self._get_topobrain_links(attribute, value, entity_id)
            investigation = self._suggest_investigation(attribute, value)

            confidence = min(score / 2.0, 0.99)
            rank = i + 1

            hypotheses.append(
                {
                    "rank": rank,
                    "attribute": attribute,
                    "over_represented_value": value,
                    "confidence": round(confidence, 3),
                    "description": description,
                    "entity_id": entity_id,
                    "diff_score": diff["score"],
                    "diff_details": diff.get("details", {}),
                    "topobrain_links": topo_links,
                    "investigation_steps": investigation["steps"],
                    "investigation_type": investigation["type"],
                }
            )

        hypotheses.sort(key=lambda h: h["confidence"], reverse=True)
        for i, h in enumerate(hypotheses):
            h["rank"] = i + 1

        return hypotheses

    def _generate_description(
        self,
        attribute: str,
        value: str,
        entity_id: str,
        diff: dict[str, Any],
    ) -> str:
        """Generate a human-readable hypothesis description."""
        details = diff.get("details", {})
        ratio = details.get("over_rep_ratio", "N/A")
        return (
            f"Attribute '{attribute}' with value '{value}' is over-represented "
            f"in failures affecting {entity_id} "
            f"({ratio}x more frequent than normal). "
            f"This may indicate a causal link to the root cause."
        )

    def _get_topobrain_links(
        self,
        attribute: str,
        value: str,
        entity_id: str,
    ) -> list[dict[str, Any]]:
        """Get TopoBrain cross-links for the hypothesis.

        Returns mock topology links connecting the attribute value
        to the affected entity and related infrastructure.
        """
        return [
            {
                "source_entity": entity_id,
                "relationship": "HAS_ATTRIBUTE",
                "target_entity": f"{attribute}:{value}",
                "layer": "attribute",
            },
            {
                "source_entity": f"{attribute}:{value}",
                "relationship": "AFFECTS",
                "target_entity": entity_id,
                "layer": "causal",
                "note": "Mock link — TopoBrain v2 integration pending",
            },
        ]

    def _suggest_investigation(
        self,
        attribute: str,
        value: str,
    ) -> dict[str, Any]:
        """Suggest investigation steps based on attribute type."""
        guide = INVESTIGATION_GUIDES.get(attribute.lower(), INVESTIGATION_GUIDES["default"])

        steps = list(guide["steps"])
        steps.insert(
            0,
            f"Verify that {attribute}={value} is abnormal (compare with historical baseline)",
        )

        return {
            "type": guide["type"],
            "steps": steps,
        }
