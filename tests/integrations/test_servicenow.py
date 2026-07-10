"""
OmniWatch 2.0 — Integrations (ServiceNow)
Component: ServiceNowIntegration Tests
Layer: Enterprise
Phase: 6
Purpose: Tests for ServiceNow CMDB and incident integration
Inputs: Mock HTTP responses
Outputs: Test assertions for CMDB push, incident creation, and sync
"""

import pytest
from unittest.mock import MagicMock, patch

from integrations.servicenow import ServiceNowIntegration


@pytest.fixture
def integration():
    """ServiceNowIntegration with mocked HTTP."""
    return ServiceNowIntegration(
        base_url="https://test-instance.service-now.com",
        username="admin",
        password="secret"
    )


class TestPushToCMDB:
    """Tests for pushing entities to ServiceNow CMDB."""

    @patch("integrations.servicenow.requests.post")
    def test_push_to_cmdb(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"sys_id": "cmdb-123"}
        mock_post.return_value = mock_response

        intg = ServiceNowIntegration(
            base_url="https://test.service-now.com",
            username="admin",
            password="secret"
        )

        result = intg.push_to_cmdb(
            entity_id="svc-payments-api",
            entity_type="Service",
            name="payments-api",
            attributes={"status": "active", "criticality": "high"}
        )

        assert result["sys_id"] == "cmdb-123"
        mock_post.assert_called_once()


class TestCreateIncident:
    """Tests for creating ServiceNow incidents from OmniWatch problems."""

    @patch("integrations.servicenow.requests.post")
    def test_create_incident(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"number": "INC0012345"}
        mock_post.return_value = mock_response

        intg = ServiceNowIntegration(
            base_url="https://test.service-now.com",
            username="admin",
            password="secret"
        )

        result = intg.create_incident(
            incident_id="INC-2026-07-001",
            title="Database latency spike",
            severity="P1",
            description="PostgreSQL p99 latency exceeded 1240ms"
        )

        assert result["number"] == "INC0012345"
        mock_post.assert_called_once()


class TestSyncIncidents:
    """Tests for bidirectional incident sync from ServiceNow."""

    @patch("integrations.servicenow.requests.get")
    def test_sync_incidents(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": [
                {"sys_id": "sn-001", "number": "INC0012345", "state": "1"},
                {"sys_id": "sn-002", "number": "INC0012346", "state": "2"}
            ]
        }
        mock_get.return_value = mock_response

        intg = ServiceNowIntegration(
            base_url="https://test.service-now.com",
            username="admin",
            password="secret"
        )

        result = intg.sync_incidents()

        assert len(result) == 2
        assert result[0]["number"] == "INC0012345"
        assert result[1]["number"] == "INC0012346"
        mock_get.assert_called_once()
