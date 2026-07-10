"""
OmniWatch 2.0 — Integrations (Terraform Cloud)
Component: TerraformCloudIntegration
Layer: Enterprise
Phase: 6
Purpose: Terraform Cloud plan/apply triggers and state drift detection
Inputs: OmniWatch drift detection events, approval workflows
Outputs: Terraform run IDs, state snapshots, workspace lists
"""

import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)


class TerraformCloudIntegration:
    """Terraform Cloud integration for infrastructure-as-code operations.

    Provides methods to:
    - Trigger plan runs from drift detection
    - Trigger apply runs after human approval
    - Retrieve current state for drift comparison
    - List and manage workspaces
    """

    def __init__(
        self,
        base_url: str,
        token: str
    ):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json"
        }

    def _api(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> requests.Response:
        """Make an API call to Terraform Cloud.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., /api/v2/workspaces)
            **kwargs: Additional arguments passed to requests

        Returns:
            requests.Response object
        """
        url = f"{self.base_url}{path}"
        kwargs.setdefault("headers", self.headers)

        method_map = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "DELETE": requests.delete
        }

        func = method_map.get(method.upper())
        if not func:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response = func(url, **kwargs)
        response.raise_for_status()
        return response

    def trigger_plan(self, workspace: str) -> dict:
        """Trigger a Terraform plan run.

        Initiates a plan run for the specified workspace, typically
        triggered by drift detection events.

        Args:
            workspace: Workspace name or ID

        Returns:
            dict with run ID and status
        """
        payload = {
            "data": {
                "attributes": {
                    "is-destroy": False,
                    "message": "OmniWatch drift detection triggered plan"
                },
                "type": "runs"
            }
        }

        logger.info("Triggering Terraform plan for workspace: %s", workspace)

        response = self._api(
            "POST",
            f"/api/v2/workspaces/{workspace}/runs",
            json=payload
        )

        result = response.json()
        run_id = result.get("data", {}).get("id")
        logger.info("Triggered plan run %s for workspace %s", run_id, workspace)

        return result.get("data", {})

    def trigger_apply(self, workspace: str, run_id: str) -> dict:
        """Trigger a Terraform apply run after approval.

        Applies a previously planned run, typically after human approval
        workflow completion.

        Args:
            workspace: Workspace name or ID
            run_id: Run ID from a previous plan

        Returns:
            dict with apply run ID and status
        """
        payload = {
            "data": {
                "attributes": {
                    "comment": "OmniWatch approved apply"
                },
                "relationships": {
                    "run": {
                        "data": {
                            "type": "runs",
                            "id": run_id
                        }
                    }
                },
                "type": "apply-runs"
            }
        }

        logger.info("Triggering Terraform apply for workspace %s, run %s", workspace, run_id)

        response = self._api(
            "POST",
            f"/api/v2/workspaces/{workspace}/actions/apply",
            json=payload
        )

        result = response.json()
        apply_id = result.get("data", {}).get("id")
        logger.info("Triggered apply run %s for workspace %s", apply_id, workspace)

        return result.get("data", {})

    def get_state(self, workspace: str) -> dict:
        """Retrieve current Terraform state for drift detection.

        Gets the current state of infrastructure in the workspace
        to compare against declared state.

        Args:
            workspace: Workspace name or ID

        Returns:
            dict with state serial, resources, and metadata
        """
        logger.info("Retrieving state for workspace: %s", workspace)

        response = self._api(
            "GET",
            f"/api/v2/workspaces/{workspace}/state"
        )

        state = response.json()
        logger.info(
            "Retrieved state for workspace %s (serial: %s)",
            workspace,
            state.get("serial")
        )

        return state

    def list_workspaces(self) -> list:
        """List all Terraform Cloud workspaces.

        Returns:
            list of workspace objects
        """
        logger.info("Listing Terraform Cloud workspaces")

        response = self._api(
            "GET",
            "/api/v2/organizations/omniwatch/workspaces"
        )

        data = response.json()
        workspaces = data.get("data", [])

        logger.info("Found %d workspaces", len(workspaces))

        return workspaces