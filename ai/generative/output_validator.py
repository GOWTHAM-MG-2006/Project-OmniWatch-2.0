"""OmniWatch 2.0 — NeuroEngine
Component: Output Validator
Layer: 6
Phase: 2
Purpose: Validates LLM output against RootCauseObject to detect hallucinated content
Inputs: LLM response text + RootCauseObject dict
Outputs: Dict with valid (bool), errors (list), warnings (list), score (float)"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

SEVERITY_LEVELS = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}


class OutputValidator:
    """Validates LLM-generated text against the source RootCauseObject.

    Checks for:
    - Entity names mentioned in response that exist in blast_radius
    - Numeric claims (user counts, percentages, latencies) within plausible range
    - Severity level consistency
    - Evidence chain references
    """

    def validate(
        self, llm_response: str, root_cause_object: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate an LLM response against its source RootCauseObject.

        Args:
            llm_response: The raw text output from the LLM.
            root_cause_object: The RootCauseObject that was used to generate the response.

        Returns:
            Dict with keys:
                valid (bool): True if no critical errors.
                errors (list[str]): Critical validation failures.
                warnings (list[str]): Non-critical observations.
                score (float): 0.0 to 1.0 validation score.
                details (dict): Per-check breakdown.
        """
        errors: list[str] = []
        warnings: list[str] = []
        details: dict[str, Any] = {}

        # 1. Entity validation
        entity_result = self._validate_entities(llm_response, root_cause_object)
        details["entities"] = entity_result
        errors.extend(entity_result.get("errors", []))
        warnings.extend(entity_result.get("warnings", []))

        # 2. Numeric claim validation
        numeric_result = self._validate_numeric_claims(llm_response, root_cause_object)
        details["numeric"] = numeric_result
        errors.extend(numeric_result.get("errors", []))
        warnings.extend(numeric_result.get("warnings", []))

        # 3. Severity validation
        severity_result = self._validate_severity(llm_response, root_cause_object)
        details["severity"] = severity_result
        errors.extend(severity_result.get("errors", []))
        warnings.extend(severity_result.get("warnings", []))

        # 4. Evidence reference validation
        evidence_result = self._validate_evidence_refs(llm_response, root_cause_object)
        details["evidence"] = evidence_result
        warnings.extend(evidence_result.get("warnings", []))

        # 5. Confidence score validation
        confidence_result = self._validate_confidence(llm_response, root_cause_object)
        details["confidence"] = confidence_result
        warnings.extend(confidence_result.get("warnings", []))

        # Compute score: 1.0 minus penalties
        penalty = min(1.0, len(errors) * 0.2 + len(warnings) * 0.05)
        score = max(0.0, 1.0 - penalty)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": round(score, 3),
            "details": details,
        }

    def _extract_entities_from_text(self, text: str) -> set[str]:
        """Extract entity-like identifiers from text.

        Looks for patterns like service names, database names, hostnames.
        """
        # Match common entity patterns: word-word-word, service-name, etc.
        patterns = [
            r'\b([a-z][a-z0-9]*(?:-[a-z][a-z0-9]*){1,5})\b',
            r'\b([A-Z][a-zA-Z]+(?:-[A-Z][a-zA-Z]+)+)\b',
        ]
        entities = set()
        for pattern in patterns:
            entities.update(re.findall(pattern, text))
        return entities

    def _validate_entities(
        self, response: str, rco: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate that entities mentioned in the response exist in the RCO."""
        root_cause_entity = rco.get("root_cause", {}).get("entity", "")
        blast_entities = {
            b.get("entity", "") for b in rco.get("blast_radius", [])
        }
        known_entities = blast_entities | {root_cause_entity} if root_cause_entity else blast_entities

        if not known_entities:
            return {"errors": [], "warnings": ["No entities in RCO to validate against"], "found": []}

        response_lower = response.lower()
        found = []
        for entity in known_entities:
            if entity and entity.lower() in response_lower:
                found.append(entity)

        # Check for entity-like names in response that aren't in the RCO
        extracted = self._extract_entities_from_text(response)
        unknown = extracted - known_entities - {"omniwatch", "incident", "analysis", "root-cause"}

        warnings = []
        if unknown and len(unknown) > 2:
            # Only warn if many unknown entities suggest hallucination
            sample = list(unknown)[:5]
            warnings.append(
                f"Response mentions {len(unknown)} entities not in RCO "
                f"(samples: {', '.join(sample)}). Possible hallucination."
            )

        return {"found": found, "unknown": list(unknown), "errors": [], "warnings": warnings}

    def _validate_numeric_claims(
        self, response: str, rco: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate numeric claims in the response against RCO values."""
        errors = []
        warnings = []

        biz = rco.get("business_impact", {})
        rco_users = biz.get("affected_users", 0)
        rco_revenue = biz.get("estimated_revenue_at_risk_usd_per_hour", 0)

        # Extract user count mentions (e.g., "12,400 users" or "12400 users")
        user_patterns = re.findall(r'(\d[\d,]*)\s*(?:users?|people|customers)', response)
        for match in user_patterns:
            claimed = int(match.replace(",", ""))
            if rco_users > 0 and claimed > 0:
                ratio = abs(claimed - rco_users) / max(rco_users, 1)
                if ratio > 0.5:
                    errors.append(
                        f"User count claim '{claimed}' deviates >50% from RCO value {rco_users}"
                    )
                elif ratio > 0.2:
                    warnings.append(
                        f"User count claim '{claimed}' differs from RCO value {rco_users} "
                        f"by {ratio:.0%}"
                    )

        # Extract revenue mentions (e.g., "$84,200")
        revenue_patterns = re.findall(r'\$([\d,]+)', response)
        for match in revenue_patterns:
            claimed = int(match.replace(",", ""))
            if rco_revenue > 0 and claimed > 0:
                ratio = abs(claimed - rco_revenue) / max(rco_revenue, 1)
                if ratio > 0.5:
                    errors.append(
                        f"Revenue claim '${claimed}' deviates >50% from RCO value ${rco_revenue}"
                    )

        # Extract percentage claims
        pct_patterns = re.findall(r'(\d+(?:\.\d+)?)\s*%', response)
        for match in pct_patterns:
            claimed = float(match)
            if claimed > 100:
                errors.append(f"Invalid percentage claim: {claimed}%")
            elif claimed < 0:
                errors.append(f"Negative percentage claim: {claimed}%")

        return {"errors": errors, "warnings": warnings}

    def _validate_severity(
        self, response: str, rco: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate severity claims in the response."""
        errors = []
        warnings = []
        rco_severity = rco.get("severity", "").upper()

        if not rco_severity:
            return {"errors": [], "warnings": ["No severity in RCO"]}

        # Find severity mentions in response
        found_severities = set()
        for level in SEVERITY_LEVELS:
            if re.search(rf'\b{level}\b', response, re.IGNORECASE):
                found_severities.add(level)

        # If response mentions a different severity than the RCO
        if found_severities and rco_severity not in found_severities:
            errors.append(
                f"Response mentions severity levels {found_severities} "
                f"but RCO severity is {rco_severity}"
            )

        return {"found": list(found_severities), "errors": errors, "warnings": warnings}

    def _validate_evidence_refs(
        self, response: str, rco: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate evidence chain references in the response."""
        warnings = []
        evidence_chain = rco.get("evidence_chain", [])

        if not evidence_chain:
            return {"warnings": ["No evidence chain in RCO to validate"]}

        # Check for evidence_id references in the response
        evidence_ids = {e.get("evidence_id", "") for e in evidence_chain}
        referenced = {eid for eid in evidence_ids if eid and eid in response}

        if not referenced and len(evidence_ids) > 0:
            warnings.append(
                "Response does not reference any evidence_id from the chain. "
                "Consider grounding claims in specific evidence."
            )

        return {"referenced": list(referenced), "warnings": warnings}

    def _validate_confidence(
        self, response: str, rco: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate confidence claims in the response."""
        warnings = []
        rco_confidence = rco.get("confidence", 0)

        if not rco_confidence:
            return {"warnings": ["No confidence in RCO"]}

        # Extract confidence mentions (e.g., "94%" or "confidence of 0.94")
        conf_patterns = re.findall(
            r'confidence\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*%', response, re.IGNORECASE
        )
        for match in conf_patterns:
            claimed_pct = float(match)
            claimed = claimed_pct / 100
            if abs(claimed - rco_confidence) > 0.15:
                warnings.append(
                    f"Confidence claim {claimed_pct:.0f}% differs significantly "
                    f"from RCO value {rco_confidence:.0%}"
                )

        return {"warnings": warnings}
