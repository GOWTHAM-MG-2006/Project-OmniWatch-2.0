"""
OmniWatch 2.0 — Integrations (GitLab)
Component: GitLabIntegration
Layer: Enterprise
Phase: 6
Purpose: GitLab issue creation, deployment linking, and webhook handling
Inputs: OmniWatch incidents, deployments, webhook payloads
Outputs: GitLab issues, deployment records, validated webhook events
"""

import hashlib
import hmac
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

SEVERITY_LABELS = {
    "P1": ["incident", "critical"],
    "P2": ["incident", "high"],
    "P3": ["incident", "medium"],
    "P4": ["incident", "low"],
}


class GitLabIntegration:
    """GitLab issue creation and webhook handling.

    Provides methods to:
    - Auto-create issues from OmniWatch incidents with severity labels
    - Link commits to deployments via deploy events
    - Receive and verify webhook payloads with HMAC signatures
    """

    def __init__(
        self,
        api_base: str,
        token: str,
        webhook_secret: str,
    ):
        self.api_base = api_base.rstrip("/")
        self.webhook_secret = webhook_secret.encode()
        self.headers = {
            "PRIVATE-TOKEN": token,
            "Content-Type": "application/json",
        }

    def create_issue(
        self,
        title: str,
        description: str,
        labels: Optional[list[str]] = None,
        severity: Optional[str] = None,
    ) -> dict:
        """Create a GitLab issue from an OmniWatch incident.

        Args:
            title: Issue title (typically includes severity prefix)
            description: Issue description with incident summary
            labels: Explicit label list
            severity: OmniWatch severity (P1-P4) — auto-maps to labels if provided

        Returns:
            dict with issue iid and other response data
        """
        final_labels = list(labels or [])
        if severity and severity in SEVERITY_LABELS:
            for lbl in SEVERITY_LABELS[severity]:
                if lbl not in final_labels:
                    final_labels.append(lbl)

        payload = {
            "title": title,
            "description": description,
            "labels": ",".join(final_labels),
        }

        logger.info("Creating GitLab issue: %s (severity: %s)", title, severity)

        response = requests.post(
            f"{self.api_base}/projects/{{project_id}}/issues",
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()

        result = response.json()
        logger.info("Created GitLab issue #%s", result.get("iid"))
        return result

    def link_deployment(
        self,
        commit_sha: str,
        environment: str,
    ) -> dict:
        """Link a commit to a deployment on GitLab.

        Args:
            commit_sha: Git commit SHA to deploy
            environment: Deployment environment (e.g., production, staging)

        Returns:
            dict with deployment ID and status
        """
        payload = {
            "sha": commit_sha,
            "ref": commit_sha,
            "environment": environment,
            "status": "running",
        }

        logger.info(
            "Linking deployment %s to environment %s", commit_sha, environment
        )

        response = requests.post(
            f"{self.api_base}/projects/{{project_id}}/deployments",
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()

        result = response.json()
        logger.info("Created deployment ID %s", result.get("id"))
        return result

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify a GitLab webhook HMAC signature.

        Args:
            payload: Raw request body bytes
            signature: X-Gitlab-Token header value (HMAC-SHA256 hex digest)

        Returns:
            True if signature is valid
        """
        if not signature:
            return False

        expected = hmac.new(
            self.webhook_secret, payload, hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    def receive_webhook(
        self,
        event_type: str,
        payload: dict,
    ) -> dict:
        """Process an incoming GitLab webhook event.

        Args:
            event_type: X-Gitlab-Event header value
            payload: Parsed JSON webhook payload

        Returns:
            dict with event_type and extracted action details
        """
        object_kind = payload.get("object_kind", "unknown")

        logger.info("Received GitLab webhook: %s/%s", event_type, object_kind)

        result = {
            "event_type": event_type,
            "object_kind": object_kind,
            "processed": True,
        }

        if object_kind == "push":
            result["commits"] = [
                {
                    "sha": c.get("id"),
                    "message": c.get("message"),
                    "author": c.get("author", {}).get("name"),
                }
                for c in payload.get("commits", [])
            ]
        elif object_kind == "merge_request":
            mr = payload.get("object_attributes", {})
            result["mr_iid"] = mr.get("iid")
            result["mr_title"] = mr.get("title")
            result["mr_url"] = mr.get("url")
        elif object_kind == "issue":
            issue = payload.get("object_attributes", {})
            result["issue_iid"] = issue.get("iid")
            result["issue_title"] = issue.get("title")

        return result
