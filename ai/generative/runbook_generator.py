"""OmniWatch 2.0 — NeuroEngine
Component: Runbook Generator
Layer: 6
Phase: 2
Purpose: Generates step-by-step remediation runbooks from RootCauseObject
Inputs: RootCauseObject dict + optional LLM output dict
Outputs: Markdown-formatted runbook string"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Entity-type-specific command templates
ENTITY_COMMANDS: dict[str, dict[str, list[str]]] = {
    "Database": {
        "verify": [
            "Check database connectivity: `pg_isready -h {entity} -p 5432`",
            "Check active connections: `SELECT count(*) FROM pg_stat_activity;`",
            "Check slow queries: `SELECT * FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '5 seconds';`",
        ],
        "mitigate": [
            "Kill long-running queries if blocking: `SELECT pg_terminate_backend(pid);`",
            "Check disk space: `df -h /var/lib/postgresql/data`",
            "Restart connection pooler if applicable",
        ],
        "fix": [
            "Apply missing index if query-related",
            "Increase connection pool size if exhaustion detected",
            "Scale up CPU/memory if resource-bound",
            "Rollback recent schema changes if correlated",
        ],
    },
    "Service": {
        "verify": [
            "Check service health: `curl -s http://{entity}/health`",
            "Check pod status: `kubectl get pods -l app={entity}`",
            "Check recent logs: `kubectl logs -l app={entity} --tail=100`",
        ],
        "mitigate": [
            "Restart the service: `kubectl rollout restart deployment/{entity}`",
            "Scale up replicas: `kubectl scale deployment/{entity} --replicas=<N>`",
            "Check resource limits: `kubectl describe pod <pod-name>`",
        ],
        "fix": [
            "Rollback to previous version if deployment-related",
            "Fix configuration and reapply",
            "Update resource requests/limits",
            "Check for memory leaks in application logs",
        ],
    },
    "Host": {
        "verify": [
            "Check host uptime: `uptime`",
            "Check CPU usage: `top -bn1 | head -20`",
            "Check memory: `free -h`",
            "Check disk I/O: `iostat -x 1 5`",
        ],
        "mitigate": [
            "Identify top CPU consumers: `ps aux --sort=-%cpu | head -10`",
            "Identify top memory consumers: `ps aux --sort=-%mem | head -10`",
            "Check for OOM kills: `dmesg | grep -i 'out of memory'`",
        ],
        "fix": [
            "Restart resource-heavy processes",
            "Scale horizontally if consistently overloaded",
            "Review and adjust resource limits",
            "Check for runaway processes or memory leaks",
        ],
    },
}

DEFAULT_COMMANDS = {
    "verify": [
        "Check service status and health endpoints",
        "Review recent logs for errors or warnings",
        "Verify network connectivity to dependent services",
    ],
    "mitigate": [
        "Restart the affected component",
        "Check resource utilization (CPU, memory, disk)",
        "Review recent configuration changes",
    ],
    "fix": [
        "Apply the recommended fix from root cause analysis",
        "Rollback recent changes if correlated with the incident",
        "Update monitoring thresholds if false positive",
    ],
}


class RunbookGenerator:
    """Generates step-by-step remediation runbooks.

    Produces structured runbooks with: prerequisites, issue verification,
    blast radius assessment, mitigation steps, fix application, and
    resolution verification. Commands are entity-type-specific.
    """

    def generate(
        self,
        root_cause_object: dict[str, Any],
        llm_output: dict[str, Any] | None = None,
    ) -> str:
        """Generate a remediation runbook.

        Args:
            root_cause_object: The RootCauseObject dict.
            llm_output: Optional LLM-generated runbook content to include.

        Returns:
            Markdown-formatted runbook.
        """
        sections = [
            self._header(root_cause_object),
            self._prerequisites(root_cause_object),
            self._verify_issue(root_cause_object),
            self._assess_blast_radius(root_cause_object),
            self._mitigate(root_cause_object),
            self._apply_fix(root_cause_object),
            self._verify_resolution(root_cause_object),
        ]

        if llm_output and llm_output.get("response"):
            sections.append(self._llm_notes(llm_output))

        sections.append(self._footer(root_cause_object))

        return "\n\n".join(s for s in sections if s)

    def _header(self, rco: dict[str, Any]) -> str:
        """Generate runbook header."""
        problem_id = rco.get("problem_id", "PRB-UNKNOWN")
        severity = rco.get("severity", "UNKNOWN")
        rc = rco.get("root_cause", {})
        entity = rc.get("entity", "unknown")
        entity_type = rc.get("entity_type", "unknown")
        ts = rco.get("analysis_timestamp", "N/A")

        return (
            f"# Remediation Runbook: {problem_id}\n\n"
            f"**Severity:** {severity}  \n"
            f"**Root Cause Entity:** `{entity}` ({entity_type})  \n"
            f"**Generated:** {ts}  \n"
            f"**Confidence:** {rco.get('confidence', 0):.0%}"
        )

    def _prerequisites(self, rco: dict[str, Any]) -> str:
        """List prerequisites before starting remediation."""
        lines = [
            "## Prerequisites\n",
            "Before executing this runbook, ensure you have:\n",
            "- [ ] Access to the affected system (`{entity}`)".format(
                entity=rco.get("root_cause", {}).get("entity", "target system")
            ),
            "- [ ] Appropriate permissions (cluster-admin or equivalent)",
            "- [ ] Access to monitoring dashboards for verification",
            "- [ ] Communication channel open (Slack/Teams) for coordination",
            "- [ ] Current deployment version noted for rollback if needed",
        ]

        severity = rco.get("severity", "UNKNOWN")
        if severity in ("CRITICAL", "HIGH"):
            lines.append(
                "\n> **WARNING:** This is a high-severity incident. "
                "Consider notifying stakeholders before taking action."
            )

        return "\n".join(lines)

    def _verify_issue(self, rco: dict[str, Any]) -> str:
        """Generate issue verification steps."""
        rc = rco.get("root_cause", {})
        entity = rc.get("entity", "unknown")
        entity_type = rc.get("entity_type", "unknown")
        metric = rc.get("metric", "unknown")
        deviation = rc.get("deviation", "N/A")

        commands = ENTITY_COMMANDS.get(entity_type, DEFAULT_COMMANDS)

        lines = [
            "## Step 1: Verify the Issue\n",
            f"**Expected finding:** {metric} showing {deviation}\n",
            "Run the following checks:\n",
        ]

        for i, cmd in enumerate(commands["verify"], 1):
            formatted_cmd = cmd.format(entity=entity)
            lines.append(f"**{i}.** `{formatted_cmd}`")

        lines.append("\n**Expected result:** Confirm the anomaly is present and matches the root cause analysis.")

        return "\n".join(lines)

    def _assess_blast_radius(self, rco: dict[str, Any]) -> str:
        """Generate blast radius assessment steps."""
        blast = rco.get("blast_radius", [])
        biz = rco.get("business_impact", {})
        users = biz.get("affected_users", 0)

        lines = [
            "## Step 2: Assess Blast Radius\n",
        ]

        if blast:
            lines.append("Affected downstream services:\n")
            lines.append("| Service | Impact | Affected Users |")
            lines.append("|---------|--------|----------------|")
            for entry in blast:
                entity = entry.get("entity", "N/A")
                impact = entry.get("impact", "N/A")
                busers = entry.get("affected_users", 0)
                lines.append(f"| {entity} | {impact} | ~{busers:,} |")
            lines.append(f"\n**Total affected users:** ~{users:,}")
        else:
            lines.append("No downstream blast radius identified.")

        lines.append("\n**Action:** Verify downstream services are degraded as expected before proceeding.")

        return "\n".join(lines)

    def _mitigate(self, rco: dict[str, Any]) -> str:
        """Generate mitigation steps."""
        rc = rco.get("root_cause", {})
        entity = rc.get("entity", "unknown")
        entity_type = rc.get("entity_type", "unknown")

        commands = ENTITY_COMMANDS.get(entity_type, DEFAULT_COMMANDS)

        lines = [
            "## Step 3: Immediate Mitigation\n",
            "Perform these steps to reduce impact while investigating the root cause:\n",
        ]

        for i, cmd in enumerate(commands["mitigate"], 1):
            formatted_cmd = cmd.format(entity=entity)
            lines.append(f"**{i}.** `{formatted_cmd}`")

        lines.append("\n**Verify:** Check monitoring dashboards to confirm impact is reduced.")

        return "\n".join(lines)

    def _apply_fix(self, rco: dict[str, Any]) -> str:
        """Generate fix application steps."""
        rc = rco.get("root_cause", {})
        entity = rc.get("entity", "unknown")
        entity_type = rc.get("entity_type", "unknown")
        metric = rc.get("metric", "unknown")
        deviation = rc.get("deviation", "N/A")

        commands = ENTITY_COMMANDS.get(entity_type, DEFAULT_COMMANDS)

        lines = [
            "## Step 4: Apply Fix\n",
            f"Based on root cause analysis ({metric}: {deviation}):\n",
        ]

        for i, cmd in enumerate(commands["fix"], 1):
            formatted_cmd = cmd.format(entity=entity)
            lines.append(f"**{i}.** {formatted_cmd}")

        lines.append(
            "\n> **Important:** Apply one change at a time and verify its effect "
            "before proceeding to the next."
        )

        return "\n".join(lines)

    def _verify_resolution(self, rco: dict[str, Any]) -> str:
        """Generate resolution verification steps."""
        rc = rco.get("root_cause", {})
        entity = rc.get("entity", "unknown")
        metric = rc.get("metric", "unknown")

        lines = [
            "## Step 5: Verify Resolution\n",
            "After applying the fix, verify the system has recovered:\n",
            f"1. Confirm `{metric}` on `{entity}` has returned to normal baseline",
            "2. Verify all downstream services are healthy",
            "3. Check that affected users can complete their workflows",
            "4. Review monitoring for any new anomalies",
            "",
            "**Success criteria:**",
            f"- `{metric}` is within normal range",
            "- No new incidents triggered",
            "- All health checks passing",
            "- Affected user count returning to zero",
        ]

        return "\n".join(lines)

    def _llm_notes(self, llm_output: dict[str, Any]) -> str:
        """Include optional LLM-generated runbook notes."""
        response = llm_output.get("response", "")
        return (
            "## Additional Notes (AI-Generated)\n\n"
            f"{response}"
        )

    def _footer(self, rco: dict[str, Any]) -> str:
        """Generate runbook footer."""
        problem_id = rco.get("problem_id", "PRB-UNKNOWN")
        return (
            "---\n\n"
            f"*Generated by OmniWatch 2.0 NeuroEngine | "
            f"Problem: {problem_id}*\n\n"
            f"*After resolution, document the outcome in the Knowledge Base.*"
        )
