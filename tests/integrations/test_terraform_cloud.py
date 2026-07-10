"""
OmniWatch 2.0 — Integrations (Terraform Cloud)
Component: TerraformCloudIntegration Tests
Layer: Enterprise
Phase: 6
Purpose: Tests for Terraform Cloud plan/apply triggers and state drift detection
Inputs: Mock HTTP responses
Outputs: Test assertions for plan, apply, and state retrieval
"""

import pytest
from unittest.mock import MagicMock, patch

from integrations.terraform_cloud import TerraformCloudIntegration


@pytest.fixture
def integration():
    """TerraformCloudIntegration with mocked HTTP."""
    return TerraformCloudIntegration(
        base_url="https://app.terraform.io",
        token="test-token-123"
    )


class TestTriggerPlan:
    """Tests for triggering Terraform plan runs."""

    @patch("integrations.terraform_cloud.requests.post")
    def test_trigger_plan(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "data": {
                "id": "run-123",
                "type": "runs",
                "attributes": {"status": "plan_queued"}
            }
        }
        mock_post.return_value = mock_response

        intg = TerraformCloudIntegration(
            base_url="https://app.terraform.io",
            token="test-token"
        )

        result = intg.trigger_plan(workspace="payments-infra")

        assert result["id"] == "run-123"
        mock_post.assert_called_once()


class TestTriggerApply:
    """Tests for triggering Terraform apply after approval."""

    @patch("integrations.terraform_cloud.requests.post")
    def test_trigger_apply(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "data": {
                "id": "run-456",
                "type": "apply-runs",
                "attributes": {"status": "apply_queued"}
            }
        }
        mock_post.return_value = mock_response

        intg = TerraformCloudIntegration(
            base_url="https://app.terraform.io",
            token="test-token"
        )

        result = intg.trigger_apply(workspace="payments-infra", run_id="run-123")

        assert result["id"] == "run-456"
        mock_post.assert_called_once()


class TestGetState:
    """Tests for retrieving Terraform workspace state."""

    @patch("integrations.terraform_cloud.requests.get")
    def test_get_state(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "serial": 1,
            "terraform_version": "1.5.0",
            "resources": [
                {"type": "aws_instance", "name": "web", "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]"}
            ]
        }
        mock_get.return_value = mock_response

        intg = TerraformCloudIntegration(
            base_url="https://app.terraform.io",
            token="test-token"
        )

        result = intg.get_state(workspace="payments-infra")

        assert result["serial"] == 1
        assert len(result["resources"]) == 1
        mock_get.assert_called_once()