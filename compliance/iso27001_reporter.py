"""
OmniWatch 2.0 — Compliance
Component: ISO27001 Annex A Evidence Report Generator
Layer: Enterprise (Phase 6)
Purpose: Generate ISO 27001 Annex A evidence packages mapping OmniWatch actions to controls
Inputs: AuditLogger events from ClickHouse audit_log table
Outputs: Markdown-formatted ISO 27001 evidence report
"""

from datetime import datetime, timezone, timedelta
from typing import Any

from compliance.audit_logger import AuditLogger

ISO27001_CONTROLS: dict[str, dict[str, Any]] = {
    "A.9.1": {
        "name": "Access Control",
        "description": "Access control policy shall be established, documented, and reviewed.",
        "event_types": ["login", "logout"],
    },
    "A.9.2": {
        "name": "User Access Management",
        "description": "User access provisioning and de-provisioning shall follow a formal process.",
        "event_types": ["login"],
    },
    "A.9.4": {
        "name": "System Access Control",
        "description": "Access to system services and applications shall be restricted.",
        "event_types": ["api_call"],
    },
    "A.12.1": {
        "name": "Operational Procedures and Responsibilities",
        "description": "Remediation actions shall be performed according to documented procedures.",
        "event_types": ["remediation_action"],
    },
    "A.12.4": {
        "name": "Logging and Monitoring",
        "description": "Event logs shall be produced, retained, and reviewed regularly.",
        "event_types": ["login", "logout", "api_call", "remediation_action", "config_change", "policy_evaluation"],
    },
    "A.14.2": {
        "name": "Secure Development",
        "description": "Changes to systems within the development lifecycle shall be controlled.",
        "event_types": ["config_change"],
    },
    "A.16.1": {
        "name": "Incident Management",
        "description": "Security events shall be assessed and responded to in a timely manner.",
        "event_types": ["remediation_action"],
    },
}


class ISO27001Reporter:
    """Generates ISO 27001 Annex A evidence packages from audit log data."""

    def __init__(self):
        self.audit_logger = AuditLogger()

    def generate_report(self, lookback_days: int = 30) -> str:
        """Generate an ISO 27001 Annex A evidence report.

        Args:
            lookback_days: Number of days to look back for evidence (default 30).

        Returns:
            Markdown-formatted ISO 27001 evidence report.
        """
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")

        stats = self.audit_logger.get_stats(start_date=start_date, end_date=end_date)

        sections = [
            self._header(now),
            self._annex_a_mapping(stats),
            self._evidence_snapshots(stats),
            self._risk_assessment(stats),
            self._treatment_plan(),
        ]

        return "\n\n".join(sections)

    def _header(self, now: datetime) -> str:
        return (
            f"# ISO 27001 Annex A Evidence Report\n\n"
            f"**Organization:** OmniWatch 2.0\n"
            f"**Standard:** ISO/IEC 27001:2022\n"
            f"**Report Period:** Last 30 days\n"
            f"**Generated:** {now.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )

    def _annex_a_mapping(self, stats: dict[str, int]) -> str:
        lines = [
            "## Annex A Control Mapping\n",
            "| Control | Name | Related Events | Evidence Count | Status |",
            "|---------|------|----------------|----------------|--------|",
        ]

        for control_id, info in ISO27001_CONTROLS.items():
            related = info["event_types"]
            count = sum(stats.get(et, 0) for et in related)
            status = "EVIDENT" if count > 0 else "NO DATA"
            lines.append(
                f"| {control_id} | {info['name']} | {', '.join(related)} | {count} | {status} |"
            )

        return "\n".join(lines)

    def _evidence_snapshots(self, stats: dict[str, int]) -> str:
        lines = ["## Evidence Snapshots\n"]

        for control_id, info in ISO27001_CONTROLS.items():
            lines.append(f"### {control_id} — {info['name']}\n")
            lines.append(f"*{info['description']}*\n")
            related = info["event_types"]
            count = sum(stats.get(et, 0) for et in related)
            lines.append(f"**Event count:** {count}\n")
            lines.append(
                "**Evidence source:** `omniwatch.audit_log` table in ClickHouse\n"
            )
            lines.append("---\n")

        return "\n".join(lines)

    def _risk_assessment(self, stats: dict[str, int]) -> str:
        total = sum(stats.values())
        failed = stats.get("failure", 0) + stats.get("denied", 0)

        lines = [
            "## Risk Assessment\n",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Audit Events | {total} |",
            f"| Failed/Denied Events | {failed} |",
            f"| Failure Rate | {(failed / total * 100) if total > 0 else 0:.2f}% |",
        ]

        return "\n".join(lines)

    def _treatment_plan(self) -> str:
        return (
            "## Treatment Plan\n\n"
            "1. Continue collecting audit events for all 7 ISO 27001 Annex A control areas.\n"
            "2. Review quarterly to ensure evidence coverage remains complete.\n"
            "3. Extend lookback period to 90 days for formal audit engagement.\n"
            "4. Map evidence to internal risk register for treatment tracking."
        )
