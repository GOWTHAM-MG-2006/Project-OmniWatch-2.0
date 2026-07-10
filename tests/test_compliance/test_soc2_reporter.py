"""
OmniWatch 2.0 — Compliance
Component: SOC2 Reporter Tests
Layer: Enterprise (Phase 6)
Purpose: Unit tests for SOC2 Type II evidence report generator
Inputs: Mocked AuditLogger
Outputs: Pass/fail assertions
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from compliance.soc2_reporter import SOC2Reporter


def _mock_audit_logger():
    mock = MagicMock()
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
    mock.get_stats.return_value = {
        "login": 150,
        "logout": 148,
        "api_call": 2300,
        "remediation_action": 5,
        "config_change": 12,
        "policy_evaluation": 89,
    }
    return mock


def test_generate_report_returns_markdown():
    """Report must be Markdown and contain SOC2 header and CC6.1 criteria."""
    with patch("compliance.soc2_reporter.AuditLogger") as MockAL:
        MockAL.return_value = _mock_audit_logger()
        reporter = SOC2Reporter()
        report = reporter.generate_report(lookback_days=30)

    assert isinstance(report, str)
    assert "SOC2" in report
    assert "CC6.1" in report
    assert report.startswith("#")


def test_control_assessment_includes_all_criteria():
    """All 7 SOC2 Trust Service Criteria must appear in the report."""
    criteria = ["CC6.1", "CC6.2", "CC6.3", "CC7.1", "CC7.2", "CC7.3", "CC8.1"]
    with patch("compliance.soc2_reporter.AuditLogger") as MockAL:
        MockAL.return_value = _mock_audit_logger()
        reporter = SOC2Reporter()
        report = reporter.generate_report(lookback_days=30)

    for criterion in criteria:
        assert criterion in report, f"Missing criterion {criterion} in report"


def test_report_has_timestamp():
    """Report must include a 'Generated:' timestamp line."""
    with patch("compliance.soc2_reporter.AuditLogger") as MockAL:
        MockAL.return_value = _mock_audit_logger()
        reporter = SOC2Reporter()
        report = reporter.generate_report(lookback_days=30)

    assert "Generated:" in report
