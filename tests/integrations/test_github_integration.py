"""
OmniWatch 2.0 — Integrations (GitHub)
Component: GitHubIntegration Tests
Layer: Enterprise
Phase: 6
Purpose: Tests for GitHub issue creation, deployment linking, and webhook handling
Inputs: Mock HTTP responses and HMAC signatures
Outputs: Test assertions for issue creation, labels, and webhook verification
"""

import hashlib
import hmac

import pytest
from unittest.mock import MagicMock, patch

from integrations.github_integration import GitHubIntegration


@pytest.fixture
def integration():
    """GitHubIntegration with mocked HTTP."""
    return GitHubIntegration(
        api_base="https://api.github.com",
        token="ghp_test_token_123",
        webhook_secret="my_webhook_secret",
    )


class TestCreateIssue:
    """Tests for creating GitHub issues from OmniWatch incidents."""

    @patch("integrations.github_integration.requests.post")
    def test_create_issue(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"number": 42}
        mock_post.return_value = mock_response

        intg = GitHubIntegration(
            api_base="https://api.github.com",
            token="ghp_test_token",
            webhook_secret="secret",
        )

        result = intg.create_issue(
            title="[P1] Database cascade failure",
            body="PostgreSQL p99 latency exceeded 1240ms",
            labels=["incident", "P1"],
            assignees=["sre-team"],
        )

        assert result["number"] == 42
        mock_post.assert_called_once()

    @patch("integrations.github_integration.requests.post")
    def test_create_issue_auto_labels(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"number": 43}
        mock_post.return_value = mock_response

        intg = GitHubIntegration(
            api_base="https://api.github.com",
            token="ghp_test_token",
            webhook_secret="secret",
        )

        result = intg.create_issue(
            title="[P2] Memory leak detected",
            body="Background worker memory growing",
            labels=[],
            assignees=[],
            severity="P2",
        )

        assert result["number"] == 43
        call_kwargs = mock_post.call_args
        payload = call_kwargs[1]["json"]
        assert "incident" in payload["labels"]
        assert "high" in payload["labels"]


class TestWebhookVerification:
    """Tests for HMAC webhook signature verification."""

    def test_verify_webhook_valid(self):
        intg = GitHubIntegration(
            api_base="https://api.github.com",
            token="ghp_test_token",
            webhook_secret="test_secret",
        )

        payload = b'{"action":"opened","pull_request":{"number":1}}'
        expected_sig = "sha256=" + hmac.new(
            b"test_secret", payload, hashlib.sha256
        ).hexdigest()

        assert intg.verify_webhook(payload, expected_sig) is True

    def test_verify_webhook_invalid(self):
        intg = GitHubIntegration(
            api_base="https://api.github.com",
            token="ghp_test_token",
            webhook_secret="test_secret",
        )

        payload = b'{"action":"opened"}'
        bad_sig = "sha256=" + "0" * 64

        assert intg.verify_webhook(payload, bad_sig) is False
