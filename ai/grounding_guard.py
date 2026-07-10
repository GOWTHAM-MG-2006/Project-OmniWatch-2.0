"""OmniWatch 2.0 — NeuroEngine
Component: Grounding Guard
Layer: 6
Phase: 2
Purpose: Validates all LLM outputs are evidence-backed to prevent hallucination
Inputs: LLM output dict + RootCauseObject
Outputs: Dict with grounded (bool), output, issues (list)"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class GroundingGuard:
    """Ensures LLM-generated outputs are grounded in evidence.

    Checks:
    - Evidence chain exists in the RootCauseObject
    - Response text references evidence from the chain
    - Cited entities exist in the RCO
    - Confidence claims match the RCO confidence
    """

    def validate(
        self,
        llm_output: dict[str, Any],
        root_cause_object: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate LLM output is grounded in evidence.

        Args:
            llm_output: Dict with at least 'response' key (str).
            root_cause_object: The RootCauseObject used to generate the response.

        Returns:
            Dict with keys:
                grounded (bool): True if all checks pass.
                output (str): The original or rejection response.
                issues (list[str]): List of grounding failures.
        """
        issues: list[str] = []
        response_text = llm_output.get("response", "")

        # 1. Check evidence chain exists
        evidence_chain = root_cause_object.get("evidence_chain", [])
        if not evidence_chain:
            issues.append("No evidence chain in RootCauseObject — cannot ground output")

        # 2. Check response references evidence
        if evidence_chain:
            evidence_refs = self._extract_evidence_refs(response_text)
            chain_ids = {
                e.get("evidence_id", f"step-{e.get('step', '?')}")
                for e in evidence_chain
            }
            chain_steps = {str(e.get("step", "")) for e in evidence_chain}
            if not evidence_refs:
                issues.append(
                    "Response does not reference any evidence from the chain"
                )
            else:
                unreferenced = evidence_refs - chain_ids - chain_steps
                if unreferenced:
                    issues.append(
                        f"Response references non-existent evidence: {unreferenced}"
                    )

        # 3. Check cited entities exist in RCO
        entity_issues = self._validate_entities(response_text, root_cause_object)
        issues.extend(entity_issues)

        # 4. Check confidence claims match
        confidence_issues = self._validate_confidence(response_text, root_cause_object)
        issues.extend(confidence_issues)

        grounded = len(issues) == 0
        output_text = response_text

        if not grounded:
            output_text = (
                "Insufficient Data: The generated response could not be fully "
                "grounded in available evidence. Please review the following "
                "issues before using this output."
            )
            logger.warning(
                "GroundingGuard rejected output: %s issues found", len(issues)
            )

        return {
            "grounded": grounded,
            "output": output_text,
            "issues": issues,
            "original_output": response_text,
        }

    def _extract_evidence_refs(self, text: str) -> set[str]:
        """Extract evidence references from response text."""
        refs: set[str] = set()
        # Match patterns like EVD-0001, EVD-123, evidence_id patterns
        evd_matches = re.findall(r"EVD[-_]?\d+", text, re.IGNORECASE)
        refs.update(m.upper().replace("_", "-") for m in evd_matches)
        # Match step references like "step 1", "Step 2"
        step_matches = re.findall(r"step\s+(\d+)", text, re.IGNORECASE)
        refs.update(f"step-{s}" for s in step_matches)
        return refs

    def _validate_entities(
        self, text: str, rco: dict[str, Any]
    ) -> list[str]:
        """Validate that entities mentioned in response exist in RCO."""
        issues: list[str] = []

        # Collect known entities from RCO
        known_entities: set[str] = set()
        root_cause = rco.get("root_cause", {})
        if root_cause.get("entity"):
            known_entities.add(root_cause["entity"])
        for item in rco.get("blast_radius", []):
            if item.get("entity"):
                known_entities.add(item["entity"])

        if not known_entities:
            return issues

        # Extract entity-like identifiers from text (simple heuristic)
        # Look for quoted strings or known entity names
        mentioned_entities: set[str] = set()
        for entity in known_entities:
            if entity.lower() in text.lower():
                mentioned_entities.add(entity)

        # Check if response mentions entity-like names not in RCO
        # Pattern: words with hyphens that look like service/entity names
        candidate_names = re.findall(
            r"\b([a-z]+-[a-z]+(?:-[a-z]+)*)\b", text.lower()
        )
        for name in candidate_names:
            # Skip common words that look like entity names
            skip_words = {
                "root-cause",
                "evidence-chain",
                "blast-radius",
                "insufficient-data",
                "the-response",
            }
            if name in skip_words:
                continue
            # If name looks like an entity but isn't in known list
            if name not in {e.lower() for e in known_entities} and len(name) > 5:
                # Only flag if it's a plausible entity name (has hyphens)
                if "-" in name:
                    issues.append(
                        f"Response mentions entity '{name}' not found in RootCauseObject"
                    )

        return issues

    def _validate_confidence(
        self, text: str, rco: dict[str, Any]
    ) -> list[str]:
        """Validate confidence claims in response match RCO confidence."""
        issues: list[str] = []
        rco_confidence = rco.get("confidence")

        if rco_confidence is None:
            return issues

        # Extract percentage claims from text
        pct_matches = re.findall(r"(\d+(?:\.\d+)?)\s*%", text)
        rco_pct = rco_confidence * 100

        for pct_str in pct_matches:
            try:
                pct = float(pct_str)
                # Allow ±5% tolerance for rounding
                if abs(pct - rco_pct) > 5.0 and pct > 10:
                    issues.append(
                        f"Confidence claim {pct}% does not match RCO confidence "
                        f"{rco_pct:.1f}%"
                    )
            except ValueError:
                continue

        return issues
