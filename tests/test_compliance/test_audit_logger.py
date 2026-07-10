"""
OmniWatch 2.0 — Compliance
Component: Audit Logger Tests
Layer: Enterprise (Phase 6)
Purpose: Unit tests for the audit logging system
Inputs: None (test file)
Outputs: Test results
"""

import json
from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest


class TestAuditLogger:
    """Tests for AuditLogger class."""

    @patch("compliance.audit_logger.clickhouse_connect.get_client")
    def test_log_api_call(self, mock_get_client):
        """Verify log_event calls clickhouse insert for API call events."""
        from compliance.audit_logger import AuditLogger

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        logger = AuditLogger()

        logger.log_event(
            event_type="api_call",
            user_id="user-123",
            resource_type="endpoint",
            resource_id="/api/v1/incidents",
            action="GET",
            outcome="success",
            ip_address="192.168.1.100",
            metadata={"status_code": 200, "response_time_ms": 45},
        )

        mock_client.insert.assert_called_once()
        call_args = mock_client.insert.call_args
        assert call_args[0][0] == "omniwatch.audit_log"

    @patch("compliance.audit_logger.clickhouse_connect.get_client")
    def test_log_remediation_action(self, mock_get_client):
        """Verify remediation events are logged correctly."""
        from compliance.audit_logger import AuditLogger

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        logger = AuditLogger()

        logger.log_event(
            event_type="remediation_action",
            user_id="auto-heal",
            resource_type="deployment",
            resource_id="payments-analytics",
            action="ROLLBACK",
            outcome="success",
            metadata={"from_version": "v2.1.4", "to_version": "v2.1.3"},
        )

        mock_client.insert.assert_called_once()
        call_args = mock_client.insert.call_args
        rows = call_args[0][1]
        assert len(rows) == 1
        row = rows[0]
        assert row[1] == "remediation_action"  # event_type
        assert row[2] == "auto-heal"  # user_id
        assert row[5] == "ROLLBACK"  # action
        assert row[6] == "success"  # outcome

    @patch("compliance.audit_logger.clickhouse_connect.get_client")
    def test_query_events(self, mock_get_client):
        """Verify query with filters returns events."""
        from compliance.audit_logger import AuditLogger

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.result_rows = [
            ("evt-1", "api_call", "user-123", "endpoint", "/api/v1/incidents",
             "GET", "success", "{}", "192.168.1.100",
             datetime(2026, 7, 10, 12, 0, 0)),
        ]
        mock_client.query.return_value = mock_result

        logger = AuditLogger()

        events = logger.query_events(
            start_date="2026-07-01",
            end_date="2026-07-10",
            event_type="api_call",
            user_id="user-123",
            limit=10,
        )

        assert len(events) == 1
        assert events[0]["event_type"] == "api_call"
        assert events[0]["user_id"] == "user-123"

    @patch("compliance.audit_logger.clickhouse_connect.get_client")
    def test_get_stats(self, mock_get_client):
        """Verify stats returns event counts by type."""
        from compliance.audit_logger import AuditLogger

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.result_rows = [
            ("api_call", 150),
            ("remediation_action", 25),
            ("config_change", 10),
        ]
        mock_client.query.return_value = mock_result

        logger = AuditLogger()

        stats = logger.get_stats()

        assert stats == {
            "api_call": 150,
            "remediation_action": 25,
            "config_change": 10,
        }
