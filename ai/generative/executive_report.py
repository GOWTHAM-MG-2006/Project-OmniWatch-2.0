"""OmniWatch 2.0 — NeuroEngine
Component: Executive Report Generator
Layer: 6
Phase: 2
Purpose: Generates non-technical executive-friendly incident reports
Inputs: RootCauseObject dict + optional LLM output dict
Outputs: Markdown-formatted executive report string"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ExecutiveReportGenerator:
    """Generates executive-friendly incident reports in non-technical language.

    Focuses on: what happened, business impact, what we're doing, and timeline.
    Avoids technical jargon in favor of clear business language.
    """

    def generate(
        self,
        root_cause_object: dict[str, Any],
        llm_output: dict[str, Any] | None = None,
    ) -> str:
        """Generate an executive-friendly incident report.

        Args:
            root_cause_object: The RootCauseObject dict.
            llm_output: Optional LLM-generated narrative to include.

        Returns:
            Markdown-formatted executive report.
        """
        sections = [
            self._headline(root_cause_object),
            self._impact_summary(root_cause_object),
            self._what_happened(root_cause_object),
            self._were_doing(root_cause_object),
            self._timeline(root_cause_object),
        ]

        if llm_output and llm_output.get("response"):
            sections.append(self._llm_narrative(llm_output))

        sections.append(self._footer(root_cause_object))

        return "\n\n".join(s for s in sections if s)

    def _headline(self, rco: dict[str, Any]) -> str:
        """Generate the executive headline."""
        severity = rco.get("severity", "UNKNOWN")
        problem_id = rco.get("problem_id", "N/A")
        rc = rco.get("root_cause", {})
        entity = rc.get("entity", "a system component")

        severity_narrative = {
            "CRITICAL": "A critical service disruption",
            "HIGH": "A significant service issue",
            "MEDIUM": "A moderate service degradation",
            "LOW": "A minor service issue",
            "INFO": "A service observation",
        }
        headline = severity_narrative.get(severity, "A service issue")

        return (
            f"# Executive Incident Report\n\n"
            f"**{headline}** — {problem_id}\n\n"
            f"**Status:** {severity} severity  \n"
            f"**Root Component:** {entity}"
        )

    def _impact_summary(self, rco: dict[str, Any]) -> str:
        """Generate the business impact summary."""
        biz = rco.get("business_impact", {})
        users = biz.get("affected_users", 0)
        revenue = biz.get("estimated_revenue_at_risk_usd_per_hour", 0)
        slo = biz.get("slo_breach", "N/A")

        impact_lines = ["## Business Impact\n"]

        if users > 0:
            if users >= 10000:
                impact_lines.append(
                    f"- **{users:,} customers** are experiencing degraded service"
                )
            elif users >= 1000:
                impact_lines.append(
                    f"- **~{users:,} customers** are affected"
                )
            else:
                impact_lines.append(
                    f"- **~{users} customers** are affected"
                )

        if revenue > 0:
            impact_lines.append(
                f"- **Estimated revenue impact:** ${revenue:,.0f} per hour of downtime"
            )

        if slo and slo != "N/A":
            impact_lines.append(
                f"- **Service Level Objective:** {slo}"
            )

        blast = rco.get("blast_radius", [])
        if blast:
            services = [b.get("entity", "unknown") for b in blast[:3]]
            impact_lines.append(
                f"- **Affected services:** {', '.join(services)}"
            )

        if len(impact_lines) == 1:
            impact_lines.append("- No significant business impact identified")

        return "\n".join(impact_lines)

    def _what_happened(self, rco: dict[str, Any]) -> str:
        """Explain what happened in non-technical language."""
        rc = rco.get("root_cause", {})
        entity = rc.get("entity", "a system component")
        entity_type = rc.get("entity_type", "component")
        metric = rc.get("metric", "performance metric")
        deviation = rc.get("deviation", "unusual behavior")
        confidence = rco.get("confidence", 0)

        type_narrative = {
            "Database": "a database system",
            "Service": "a backend service",
            "Host": "a server",
            "Infrastructure": "infrastructure component",
            "Process": "a background process",
            "GenAIService": "an AI service",
            "BusinessTransaction": "a business workflow",
        }
        type_text = type_narrative.get(entity_type, "a system component")

        return (
            "## What Happened\n\n"
            f"Our monitoring detected that {entity}, which is {type_text}, "
            f"experienced abnormal behavior in its {metric}. "
            f"The system observed: {deviation}.\n\n"
            f"Confidence in this diagnosis: **{confidence:.0%}**.\n\n"
            f"The issue was identified through automated root cause analysis "
            f"that traced the problem through the system dependency chain."
        )

    def _were_doing(self, rco: dict[str, Any]) -> str:
        """Describe current remediation actions."""
        severity = rco.get("severity", "UNKNOWN")

        actions = []
        if severity in ("CRITICAL", "HIGH"):
            actions = [
                "Engineering team has been automatically notified",
                "Automated health checks are running continuously",
                "If the issue is configuration-related, auto-remediation is evaluating fixes",
                "Root cause analysis is providing evidence-backed recommendations",
            ]
        else:
            actions = [
                "Monitoring the situation with automated alerts",
                "Reviewing root cause analysis recommendations",
                "Assessing whether automated remediation can resolve the issue",
            ]

        lines = ["## What We're Doing\n"]
        for action in actions:
            lines.append(f"- {action}")

        return "\n".join(lines)

    def _timeline(self, rco: dict[str, Any]) -> str:
        """Generate a simple timeline."""
        ts = rco.get("analysis_timestamp", "N/A")
        chain = rco.get("evidence_chain", [])

        lines = [
            "## Timeline\n",
            "| Time | Event |",
            "|------|-------|",
            f"| {ts} | Incident detected and analyzed |",
        ]

        for entry in chain[:5]:
            step = entry.get("step", "?")
            obs = entry.get("observation", "N/A")
            entry_ts = entry.get("timestamp", "N/A")
            # Truncate long observations
            short_obs = obs[:80] + "..." if len(obs) > 80 else obs
            lines.append(f"| {entry_ts} | Step {step}: {short_obs} |")

        return "\n".join(lines)

    def _llm_narrative(self, llm_output: dict[str, Any]) -> str:
        """Include optional LLM-generated executive narrative."""
        response = llm_output.get("response", "")
        return (
            "## Detailed Analysis\n\n"
            f"{response}"
        )

    def _footer(self, rco: dict[str, Any]) -> str:
        """Generate the report footer."""
        problem_id = rco.get("problem_id", "N/A")
        return (
            "---\n\n"
            f"*Report generated by OmniWatch 2.0 | Incident: {problem_id}*\n\n"
            "*For technical details, refer to the full Incident Summary Report.*"
        )
