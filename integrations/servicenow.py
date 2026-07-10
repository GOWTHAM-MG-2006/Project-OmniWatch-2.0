"""
OmniWatch 2.0 — Integrations (ServiceNow)
Component: ServiceNowIntegration
Layer: Enterprise
Phase: 6
Purpose: ServiceNow CMDB and incident integration
Inputs: OmniWatch entities, problems, incidents
Outputs: ServiceNow CMDB records, incidents, and sync
"""

import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)

# Entity type mapping to ServiceNow CMDB class
ENTITY_TYPE_MAP = {
    "Service": "cmdb_ci_service",
    "Host": "cmdb_ci_server",
    "Database": "cmdb_ci_db",
    "Process": "cmdb_ci_process",
    "GenAIService": "cmdb_ci_service",
    "BusinessTransaction": "cmdb_ci_service",
    "CostCenter": "cmdb_ci_cost_center",
}


class ServiceNowIntegration:
    """ServiceNow CMDB and incident integration.

    Provides methods to:
    - Push discovered entities to CMDB (auto-create CI records)
    - Create incidents from OmniWatch problems
    - Bidirectional sync: ServiceNow incidents → OmniWatch incidents
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str
    ):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _api(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> requests.Response:
        """Make an API call to ServiceNow.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., /api/now/table/cmdb_ci)
            **kwargs: Additional arguments passed to requests

        Returns:
            requests.Response object
        """
        url = f"{self.base_url}{path}"
        kwargs.setdefault("auth", self.auth)
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

    def push_to_cmdb(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        attributes: Optional[dict] = None
    ) -> dict:
        """Push an entity to ServiceNow CMDB.

        Creates or updates a Configuration Item (CI) record in ServiceNow CMDB.
        Maps entity types to ServiceNow CMDB classes.

        Args:
            entity_id: OmniWatch entity identifier
            entity_type: Entity type (Service, Host, Database, etc.)
            name: Human-readable entity name
            attributes: Additional attributes to set on the CI

        Returns:
            dict with sys_id and other response data
        """
        cmdb_class = ENTITY_TYPE_MAP.get(entity_type, "cmdb_ci")

        payload = {
            "name": name,
            "operational_status": "1",  # Operational
            "discovery_source": "OmniWatch",
            "u_entity_id": entity_id,
            "u_entity_type": entity_type
        }

        if attributes:
            for key, value in attributes.items():
                payload[f"u_{key}"] = str(value)

        logger.info(
            "Pushing entity %s to CMDB class %s",
            entity_id,
            cmdb_class
        )

        response = self._api(
            "POST",
            f"/api/now/table/{cmdb_class}",
            json=payload
        )

        result = response.json()
        sys_id = result.get("sys_id")
        logger.info("Created CMDB CI: %s (sys_id: %s)", name, sys_id)

        return result

    def create_incident(
        self,
        incident_id: str,
        title: str,
        severity: str,
        description: str
    ) -> dict:
        """Create a ServiceNow incident from an OmniWatch problem.

        Maps OmniWatch severity to ServiceNow priority:
        - P1 → 1 (Critical)
        - P2 → 2 (High)
        - P3 → 3 (Moderate)
        - P4 → 4 (Low)

        Args:
            incident_id: OmniWatch incident identifier
            title: Incident title
            severity: Severity level (P1-P4)
            description: Detailed description

        Returns:
            dict with number and sys_id
        """
        priority_map = {
            "P1": "1",
            "P2": "2",
            "P3": "3",
            "P4": "4"
        }

        payload = {
            "short_description": title,
            "description": description,
            "priority": priority_map.get(severity, "3"),
            "urgency": "1" if severity in ("P1", "P2") else "2",
            "impact": "1" if severity == "P1" else "2",
            "caller_id": "OmniWatch",
            "category": "Software",
            "subcategory": "Application",
            "u_omniwatch_incident_id": incident_id,
            "u_source": "OmniWatch"
        }

        logger.info(
            "Creating ServiceNow incident for %s (severity: %s)",
            incident_id,
            severity
        )

        response = self._api(
            "POST",
            "/api/now/table/incident",
            json=payload
        )

        result = response.json()
        number = result.get("number")
        logger.info("Created ServiceNow incident: %s", number)

        return result

    def sync_incidents(self) -> list:
        """Sync incidents from ServiceNow.

        Retrieves recent incidents from ServiceNow that were created
        or updated by OmniWatch, for bidirectional synchronization.

        Returns:
            list of incident records
        """
        query = "u_source=OmniWatch^ORDER BYsys_created_onDESC"

        logger.info("Syncing incidents from ServiceNow")

        response = self._api(
            "GET",
            "/api/now/table/incident",
            params={
                "sysparm_query": query,
                "sysparm_limit": "100"
            }
        )

        data = response.json()
        incidents = data.get("result", [])

        logger.info("Synced %d incidents from ServiceNow", len(incidents))

        return incidents
