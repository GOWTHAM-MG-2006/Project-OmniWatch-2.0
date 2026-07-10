"""
OmniWatch 2.0 — Compliance
Component: ISO27001 Reporter Tests
Layer: Enterprise (Phase 6)
Purpose: Unit tests for ISO 27001 Annex A evidence report generator
Inputs: Mocked AuditLogger
Outputs: Pass/fail assertions
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from compliance.iso27001_reporter import ISO27001Reporter


def _mock_audit_logger():
    mock = MagicMock()
    mock.get_stats.return_value = {
        "login": 150,
        "logout": 148,
        "api_call": 2300,
        "remediation_action": 5,
        "config_change": 12,
        "policy_evaluation": 89,
    }
    mock.query_events.return_value = [
        {
            "event_id": "evt-001",
            "event_type": "login",
            "user_id": "user-1",
            "resource_type": "session",
            "resource_id": "sess-1",
            "action": "LOGIN",
            "outcome": "success",
            "metadata": "{}",
            "ip_address": "10.0.0.1",
            "timestamp": datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc),
        },
        {
            "event_id": "evt-002",
            "event_type": "remediation_action",
            "user_id": "auto-heal",
            "resource_type": "deployment",
            "resource_id": "payments-v2.1.4",
            "action": "ROLLBACK",
            "outcome": "success",
            "metadata": '{"incident_id": "INC-001"}',
            "ip_address": "",
            "timestamp": datetime(2026, 7, 2, 14, 30, 0, tzinfo=timezone.utc),
        },
    ]
    return mock


def test_generate_report_returns_markdown():
    """Report must be Markdown and contain ISO 27001 header."""
    with patch("compliance.iso27001_reporter.AuditLogger") as MockAL:
        MockAL.return_value = _mock_audit_logger()
        reporter = ISO27001Reporter()
        report = reporter.generate_report(lookback_days=30)

    assert isinstance(report, str)
    assert "ISO 27001" in report
    assert report.startswith("#")


def test_report_includes_annex_a_controls():
    """All 7 Annex A controls must appear in the report."""
    controls = [
        "A.9.1",
        "A.9.2",
        "A.9.4",
        "A.12.1",
        "A.12.4",
        "A.14.2",
        "A.16.1",
    ]
    with patch("compliance.iso27001_reporter.AuditLogger") as MockAL:
        MockAL.return_value = _mock_audit_logger()
        reporter = ISO27001Reporter()
        report = reporter.generate_report(lookback_days=30)

    for control in controls:
        assert control in report, f"Missing Annex A control {control} in report"
