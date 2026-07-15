"""OmniWatch 2.0 — NeuroEngine
Component: Post-Incident Analyser
Layer: 6
Phase: 2
Purpose: Generates post-mortem reports from RootCauseObject
Inputs: RootCauseObject dict + optional LLM output dict
Outputs: Markdown-formatted post-mortem report string"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PostIncidentAnalyser:
    """Generates post-mortem (post-incident) analysis reports.

    Produces structured reports with: timeline, root cause analysis,
    impact assessment, what went well/wrong, action items, and prevention.
    """

    def generate(
        self,
        root_cause_object: dict[str, Any],
        llm_output: dict[str, Any] | None = None,
    ) -> str:
        """Generate a post-mortem report.

        Args:
            root_cause_object: The RootCauseObject dict.
            llm_output: Optional LLM-generated analysis to include.

        Returns:
            Markdown-formatted post-mortem report.
        """
        sections = [
            self._header(root_cause_object),
            self._incident_summary(root_cause_object),
            self._timeline(root_cause_object),
            self._root_cause_analysis(root_cause_object),
            self._impact(root_cause_object),
            self._what_went_well(root_cause_object),
            self._what_went_wrong(root_cause_object),
            self._action_items(root_cause_object),
            self._prevention(root_cause_object),
        ]

        if llm_output and llm_output.get("response"):
            sections.append(self._llm_analysis(llm_output))

        sections.append(self._footer(root_cause_object))

        return "\n\n".join(s for s in sections if s)

    def _header(self, rco: dict[str, Any]) -> str:
        """Generate report header."""
        problem_id = rco.get("problem_id", "PRB-UNKNOWN")
        severity = rco.get("severity", "UNKNOWN")
        ts = rco.get("analysis_timestamp", "N/A")

        return (
            f"# Post-Incident Report: {problem_id}\n\n"
            f"**Severity:** {severity}  \n"
            f"**Date:** {ts}  \n"
            f"**Status:** Analysis Complete  \n"
            f"**Prepared by:** OmniWatch 2.0 NeuroEngine"
        )

    def _incident_summary(self, rco: dict[str, Any]) -> str:
        """Generate a brief incident summary."""
        rc = rco.get("root_cause", {})
        entity = rc.get("entity", "unknown")
        entity_type = rc.get("entity_type", "unknown")
        metric = rc.get("metric", "unknown")
        deviation = rc.get("deviation", "N/A")
        confidence = rco.get("confidence", 0)
        biz = rco.get("business_impact", {})
        users = biz.get("affected_users", 0)
        revenue = biz.get("estimated_revenue_at_risk_usd_per_hour", 0)

        return (
            "## Incident Summary\n\n"
            f"| Field | Detail |\n"
            f"|-------|--------|\n"
            f"| Root Cause | `{entity}` ({entity_type}) |\n"
            f"| Metric | `{metric}` |\n"
            f"| Deviation | {deviation} |\n"
            f"| Confidence | {confidence:.0%} |\n"
            f"| Affected Users | ~{users:,} |\n"
            f"| Revenue Impact | ${revenue:,.0f}/hour |"
        )

    def _timeline(self, rco: dict[str, Any]) -> str:
        """Generate the incident timeline."""
        chain = rco.get("evidence_chain", [])
        ts = rco.get("analysis_timestamp", "N/A")

        lines = [
            "## Timeline\n",
            "| Time | Event | Evidence |",
            "|------|-------|----------|",
            f"| {ts} | Incident detected | Automated |",
        ]

        for entry in chain:
            step = entry.get("step", "?")
            obs = entry.get("observation", "N/A")
            entry_ts = entry.get("timestamp", "N/A")
            eid = entry.get("evidence_id", "N/A")
            short_obs = obs[:60] + "..." if len(obs) > 60 else obs
            lines.append(f"| {entry_ts} | Step {step}: {short_obs} | {eid} |")

        lines.append(f"| {ts} | Root cause identified | Analysis |")

        return "\n".join(lines)

    def _root_cause_analysis(self, rco: dict[str, Any]) -> str:
        """Generate detailed root cause analysis."""
        rc = rco.get("root_cause", {})
        entity = rc.get("entity", "unknown")
        entity_type = rc.get("entity_type", "unknown")
        layer = rc.get("layer", "N/A")
        metric = rc.get("metric", "unknown")
        deviation = rc.get("deviation", "N/A")
        causal_score = rc.get("causal_score", 0)
        method = rco.get("analysis_method", "N/A")

        return (
            "## Root Cause Analysis\n\n"
            f"**Method:** {method}\n\n"
            f"The root cause was identified as **`{entity}`** ({entity_type}) "
            f"at Layer {layer}.\n\n"
            f"**Key findings:**\n"
            f"- Metric `{metric}` showed deviation: {deviation}\n"
            f"- Causal confidence score: {causal_score:.4f}\n"
            f"- Analysis traced the problem through the dependency graph "
            f"to identify the originating component\n\n"
            f"**Evidence chain:** {len(rco.get('evidence_chain', []))} steps traced"
        )

    def _impact(self, rco: dict[str, Any]) -> str:
        """Generate impact assessment."""
        biz = rco.get("business_impact", {})
        users = biz.get("affected_users", 0)
        revenue = biz.get("estimated_revenue_at_risk_usd_per_hour", 0)
        slo = biz.get("slo_breach", "N/A")
        blast = rco.get("blast_radius", [])

        lines = [
            "## Impact Assessment\n",
        ]

        if users > 0:
            lines.append(f"**Users affected:** ~{users:,}")
        if revenue > 0:
            lines.append(f"**Revenue impact:** ${revenue:,.0f}/hour")
        if slo and slo != "N/A":
            lines.append(f"**SLO breach:** {slo}")

        if blast:
            lines.append(f"\n**Downstream services affected:** {len(blast)}")
            for b in blast:
                lines.append(f"- `{b.get('entity', 'N/A')}`: {b.get('impact', 'N/A')}")

        return "\n".join(lines)

    def _what_went_well(self, rco: dict[str, Any]) -> str:
        """Identify what went well during the incident."""
        confidence = rco.get("confidence", 0)
        chain = rco.get("evidence_chain", [])
        blast = rco.get("blast_radius", [])

        items = []
        if confidence >= 0.8:
            items.append(f"Root cause identified with {confidence:.0%} confidence")
        if len(chain) >= 3:
            items.append(f"Strong evidence chain ({len(chain)} steps) established")
        if len(chain) >= 1:
            items.append("Detection pipeline captured relevant signals")
        if blast and len(blast) <= 3:
            items.append("Blast radius was well-contained")
        if not items:
            items.append("Incident was detected and logged")

        lines = ["## What Went Well\n"]
        for item in items:
            lines.append(f"- {item}")
        return "\n".join(lines)

    def _what_went_wrong(self, rco: dict[str, Any]) -> str:
        """Identify what went wrong during the incident."""
        severity = rco.get("severity", "UNKNOWN")
        confidence = rco.get("confidence", 0)
        biz = rco.get("business_impact", {})
        users = biz.get("affected_users", 0)
        blast = rco.get("blast_radius", [])

        items = []
        if severity in ("CRITICAL", "HIGH"):
            items.append(f"Incident reached {severity} severity before detection")
        if confidence < 0.7:
            items.append(f"Root cause confidence was only {confidence:.0%} — uncertain diagnosis")
        if users > 5000:
            items.append(f"High user impact ({users:,} users) — insufficient preventive monitoring")
        if blast and len(blast) > 5:
            items.append(f"Wide blast radius ({len(blast)} services) — insufficient circuit breakers")
        if not items:
            items.append("Review incident timeline for improvement opportunities")

        lines = ["## What Went Wrong\n"]
        for item in items:
            lines.append(f"- {item}")
        return "\n".join(lines)

    def _action_items(self, rco: dict[str, Any]) -> str:
        """Generate action items for prevention."""
        rc = rco.get("root_cause", {})
        entity = rc.get("entity", "unknown")
        entity_type = rc.get("entity_type", "unknown")

        items = [
            f"**Immediate:** Add monitoring for `{entity}` metric deviations",
            f"**Short-term:** Create automated remediation runbook for {entity_type} failures",
            "**Medium-term:** Review and update alerting thresholds across related services",
            "**Long-term:** Implement predictive alerting for early warning",
        ]

        lines = ["## Action Items\n", "| Priority | Item | Owner | Due |", "|----------|------|-------|-----|"]
        priorities = ["P0", "P1", "P2", "P3"]
        owners = ["SRE Team", "Platform Team", "Service Owner", "SRE Lead"]
        for i, item in enumerate(items):
            lines.append(f"| {priorities[i]} | {item} | {owners[i]} | TBD |")

        return "\n".join(lines)

    def _prevention(self, rco: dict[str, Any]) -> str:
        """Generate prevention recommendations."""
        rc = rco.get("root_cause", {})
        entity_type = rc.get("entity_type", "unknown")

        recommendations = {
            "Database": [
                "Implement connection pooling with circuit breakers",
                "Add query timeout limits",
                "Set up automated failover for primary database",
                "Create capacity alerts for connection count and query latency",
            ],
            "Service": [
                "Implement health check endpoints with dependency checks",
                "Add circuit breakers for downstream calls",
                "Set up automatic scaling based on request volume",
                "Implement graceful degradation for non-critical paths",
            ],
            "Host": [
                "Implement host-level resource monitoring with auto-scaling",
                "Set up process watchdog with automatic restart",
                "Add disk space alerts with automated cleanup",
                "Implement host health scoring for proactive replacement",
            ],
        }

        recs = recommendations.get(entity_type, [
            "Add comprehensive monitoring for this entity type",
            "Implement automated health checks",
            "Create runbooks for common failure scenarios",
            "Set up alerting for early warning signs",
        ])

        lines = ["## Prevention Recommendations\n"]
        for rec in recs:
            lines.append(f"- {rec}")

        return "\n".join(lines)

    def _llm_analysis(self, llm_output: dict[str, Any]) -> str:
        """Include optional LLM-generated analysis."""
        response = llm_output.get("response", "")
        return (
            "## Additional Analysis (AI-Generated)\n\n"
            f"{response}"
        )

    def _footer(self, rco: dict[str, Any]) -> str:
        """Generate report footer."""
        problem_id = rco.get("problem_id", "PRB-UNKNOWN")
        return (
            "---\n\n"
            f"*Generated by OmniWatch 2.0 NeuroEngine | "
            f"Incident: {problem_id}*\n\n"
            f"*This post-mortem should be reviewed and approved by the incident commander "
            f"before distribution.*"
        )
