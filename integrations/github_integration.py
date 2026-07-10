"""
OmniWatch 2.0 — Integrations (GitHub)
Component: GitHubIntegration
Layer: Enterprise
Phase: 6
Purpose: GitHub issue creation, deployment linking, and webhook handling
Inputs: OmniWatch incidents, deployments, webhook payloads
Outputs: GitHub issues, deployment records, validated webhook events
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


class GitHubIntegration:
    """GitHub issue creation and webhook handling.

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
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
        severity: Optional[str] = None,
    ) -> dict:
        """Create a GitHub issue from an OmniWatch incident.

        Args:
            title: Issue title (typically includes severity prefix)
            body: Issue body with incident summary
            labels: Explicit label list
            assignees: GitHub usernames to assign
            severity: OmniWatch severity (P1-P4) — auto-maps to labels if provided

        Returns:
            dict with issue number and other response data
        """
        final_labels = list(labels or [])
        if severity and severity in SEVERITY_LABELS:
            for lbl in SEVERITY_LABELS[severity]:
                if lbl not in final_labels:
                    final_labels.append(lbl)

        payload = {"title": title, "body": body, "labels": final_labels}
        if assignees:
            payload["assignees"] = assignees

        logger.info("Creating GitHub issue: %s (severity: %s)", title, severity)

        response = requests.post(
            f"{self.api_base}/repos/{{owner}}/{{repo}}/issues",
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()

        result = response.json()
        logger.info("Created GitHub issue #%s", result.get("number"))
        return result

    def link_deployment(
        self,
        commit_sha: str,
        environment: str,
        repo: Optional[str] = None,
    ) -> dict:
        """Link a commit to a deployment on GitHub.

        Args:
            commit_sha: Git commit SHA to deploy
            environment: Deployment environment (e.g., production, staging)
            repo: Repository in owner/repo format

        Returns:
            dict with deployment ID and status
        """
        repo_path = repo or "{owner}/{repo}"
        payload = {
            "ref": commit_sha,
            "environment": environment,
            "auto_merge": False,
            "required_contexts": [],
        }

        logger.info(
            "Linking deployment %s to environment %s", commit_sha, environment
        )

        response = requests.post(
            f"{self.api_base}/repos/{repo_path}/deployments",
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()

        result = response.json()
        logger.info("Created deployment ID %s", result.get("id"))
        return result

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify a GitHub webhook HMAC signature.

        Args:
            payload: Raw request body bytes
            signature: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid
        """
        if not signature or not signature.startswith("sha256="):
            return False

        expected = hmac.new(
            self.webhook_secret, payload, hashlib.sha256
        ).hexdigest()
        received = signature.split("=", 1)[1]

        return hmac.compare_digest(expected, received)

    def receive_webhook(
        self,
        event_type: str,
        payload: dict,
    ) -> dict:
        """Process an incoming GitHub webhook event.

        Args:
            event_type: X-GitHub-Event header value
            payload: Parsed JSON webhook payload

        Returns:
            dict with event_type and extracted action details
        """
        action = payload.get("action", "unknown")

        logger.info("Received GitHub webhook: %s/%s", event_type, action)

        result = {
            "event_type": event_type,
            "action": action,
            "processed": True,
        }

        if event_type == "push":
            result["commits"] = [
                {
                    "sha": c.get("id"),
                    "message": c.get("message"),
                    "author": c.get("author", {}).get("username"),
                }
                for c in payload.get("commits", [])
            ]
        elif event_type == "pull_request":
            pr = payload.get("pull_request", {})
            result["pr_number"] = pr.get("number")
            result["pr_title"] = pr.get("title")
            result["pr_url"] = pr.get("html_url")
        elif event_type == "issues":
            issue = payload.get("issue", {})
            result["issue_number"] = issue.get("number")
            result["issue_title"] = issue.get("title")

        return result
