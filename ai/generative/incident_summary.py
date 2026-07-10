"""OmniWatch 2.0 — NeuroEngine
Component: Incident Summary Generator
Layer: 6
Phase: 2
Purpose: Generates markdown incident summaries from RootCauseObject
Inputs: RootCauseObject dict + optional LLM output dict
Outputs: Markdown-formatted incident summary string"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class IncidentSummaryGenerator:
    """Generates structured markdown incident summaries.

    Produces a human-readable report with: problem_id, severity, confidence,
    root cause table, business impact, evidence chain, and blast radius.
    """

    def generate(
        self,
        root_cause_object: dict[str, Any],
        llm_output: dict[str, Any] | None = None,
    ) -> str:
        """Generate a markdown incident summary.

        Args:
            root_cause_object: The RootCauseObject dict.
            llm_output: Optional LLM-generated analysis text to include.

        Returns:
            Markdown-formatted incident summary.
        """
        sections = [
            self._header(root_cause_object),
            self._severity_badge(root_cause_object),
            self._root_cause_table(root_cause_object),
            self._business_impact(root_cause_object),
            self._evidence_chain(root_cause_object),
            self._blast_radius(root_cause_object),
        ]

        if llm_output and llm_output.get("response"):
            sections.append(self._llm_analysis(llm_output))

        sections.append(self._footer(root_cause_object))

        return "\n\n".join(s for s in sections if s)

    def _header(self, rco: dict[str, Any]) -> str:
        """Generate the report header."""
        problem_id = rco.get("problem_id", "PRB-UNKNOWN")
        ts = rco.get("analysis_timestamp", "N/A")
        return (
            f"# Incident Report: {problem_id}\n\n"
            f"**Generated:** {ts}  \n"
            f"**Analysis Method:** {rco.get('analysis_method', 'N/A')}  \n"
            f"**Problem ID:** {problem_id}"
        )

    def _severity_badge(self, rco: dict[str, Any]) -> str:
        """Generate severity and confidence display."""
        severity = rco.get("severity", "UNKNOWN")
        confidence = rco.get("confidence", 0)
        return (
            "## Status\n\n"
            f"| Severity | Confidence |\n"
            f"|----------|------------|\n"
            f"| **{severity}** | {confidence:.0%} |"
        )

    def _root_cause_table(self, rco: dict[str, Any]) -> str:
        """Generate root cause details table."""
        rc = rco.get("root_cause", {})
        entity = rc.get("entity", "N/A")
        entity_type = rc.get("entity_type", "N/A")
        layer = rc.get("layer", "N/A")
        metric = rc.get("metric", "N/A")
        deviation = rc.get("deviation", "N/A")
        causal_score = rc.get("causal_score", 0)

        return (
            "## Root Cause\n\n"
            "| Field | Value |\n"
            "|-------|-------|\n"
            f"| Entity | `{entity}` |\n"
            f"| Type | {entity_type} |\n"
            f"| Layer | {layer} |\n"
            f"| Metric | `{metric}` |\n"
            f"| Deviation | {deviation} |\n"
            f"| Causal Score | {causal_score:.4f} |"
        )

    def _business_impact(self, rco: dict[str, Any]) -> str:
        """Generate business impact section."""
        biz = rco.get("business_impact", {})
        users = biz.get("affected_users", 0)
        revenue = biz.get("estimated_revenue_at_risk_usd_per_hour", 0)
        slo = biz.get("slo_breach", "N/A")

        return (
            "## Business Impact\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            f"| Affected Users | ~{users:,} |\n"
            f"| Revenue at Risk | ${revenue:,.0f}/hour |\n"
            f"| SLO Breach | {slo} |"
        )

    def _evidence_chain(self, rco: dict[str, Any]) -> str:
        """Generate the evidence chain section."""
        chain = rco.get("evidence_chain", [])
        if not chain:
            return "## Evidence Chain\n\nNo evidence chain available."

        lines = ["## Evidence Chain\n", "| Step | Observation | Type | ID |", "|------|-------------|------|----|"]
        for entry in chain:
            step = entry.get("step", "?")
            obs = entry.get("observation", "N/A")
            sig_type = entry.get("signal_type", "N/A")
            eid = entry.get("evidence_id", "N/A")
            lines.append(f"| {step} | {obs} | {sig_type} | {eid} |")

        return "\n".join(lines)

    def _blast_radius(self, rco: dict[str, Any]) -> str:
        """Generate the blast radius section."""
        blast = rco.get("blast_radius", [])
        if not blast:
            return "## Blast Radius\n\nNo downstream impact identified."

        lines = [
            "## Blast Radius\n",
            "| Entity | Impact | Affected Users |",
            "|--------|--------|----------------|",
        ]
        for entry in blast:
            entity = entry.get("entity", "N/A")
            impact = entry.get("impact", "N/A")
            users = entry.get("affected_users", 0)
            lines.append(f"| {entity} | {impact} | ~{users:,} |")

        total = sum(b.get("affected_users", 0) for b in blast)
        lines.append(f"\n**Total estimated affected users:** ~{total:,}")

        return "\n".join(lines)

    def _llm_analysis(self, llm_output: dict[str, Any]) -> str:
        """Include optional LLM-generated analysis."""
        response = llm_output.get("response", "")
        model = llm_output.get("model", "unknown")
        return (
            "## AI-Generated Analysis\n\n"
            f"*Model: {model}*\n\n"
            f"{response}"
        )

    def _footer(self, rco: dict[str, Any]) -> str:
        """Generate the report footer."""
        problem_id = rco.get("problem_id", "PRB-UNKNOWN")
        return (
            "---\n\n"
            f"*Generated by OmniWatch 2.0 NeuroEngine | "
            f"Problem: {problem_id}*"
        )
