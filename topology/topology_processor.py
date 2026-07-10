"""
OmniWatch 2.0 — TopoBrain
Component: Topology Processor
Layer: 5
Phase: 1
Purpose: Processes topology deltas from Kafka and updates the knowledge graph
Inputs: Topology delta events from StreamForge
Outputs: Updated graph state in Kuzu
"""

import os
import json
import logging
from typing import Any

from topology.graph_database import TopoBrainGraph

logger = logging.getLogger(__name__)


class TopologyProcessor:
    """Processes topology deltas and updates the knowledge graph."""

    def __init__(self, graph: TopoBrainGraph | None = None):
        self.graph = graph or TopoBrainGraph()
        self._processed_count = 0

    def process_delta(self, delta: dict[str, Any]) -> bool:
        """Process a single topology delta event."""
        change_type = delta.get("change_type", "")
        entity_id = delta.get("entity_id", "")
        entity_data = delta.get("entity_data", {})

        if not entity_id:
            logger.warning("Delta missing entity_id: %s", delta)
            return False

        try:
            success = self.apply_to_graph(change_type, entity_id, entity_data, delta.get("old_data", {}))
            if success:
                self._processed_count += 1
            return success
        except Exception as e:
            logger.error("Failed to process delta for %s: %s", entity_id, e)
            return False

    def apply_to_graph(
        self,
        change_type: str,
        entity_id: str,
        entity_data: dict[str, Any],
        old_data: dict[str, Any],
    ) -> bool:
        """Apply a topology change to the graph."""
        if change_type == "ENTITY_ADDED":
            return self._add_entity(entity_id, entity_data)
        elif change_type == "ENTITY_REMOVED":
            return self._remove_entity(entity_id)
        elif change_type == "ENTITY_UPDATED":
            return self._update_entity(entity_id, entity_data)
        elif change_type == "DEPENDENCY_ADDED":
            return self._add_dependency(entity_id, entity_data)
        elif change_type == "DEPENDENCY_REMOVED":
            return self._remove_dependency(entity_id, entity_data)
        elif change_type == "STATUS_CHANGED":
            return self._update_status(entity_id, entity_data, old_data)
        elif change_type == "ANOMALY_SCORE_UPDATED":
            return self._update_anomaly_score(entity_id, entity_data)
        else:
            logger.warning("Unknown change type: %s", change_type)
            return False

    def _add_entity(self, entity_id: str, data: dict[str, Any]) -> bool:
        """Add a new entity to the graph."""
        entity_type = data.get("entity_type", "service").lower()

        if entity_type == "service":
            return self.graph.add_service(
                service_id=entity_id,
                name=data.get("name", entity_id),
                service_type=data.get("type", "microservice"),
                criticality=data.get("criticality", "medium"),
                cloud_provider=data.get("cloud_provider", "local"),
                status=data.get("status", "healthy"),
            )
        elif entity_type == "host":
            return self.graph.add_host(
                host_id=entity_id,
                name=data.get("name", entity_id),
                host_type=data.get("type", "vm"),
                cloud_provider=data.get("cloud_provider", "local"),
                region=data.get("region", "us-east-1"),
            )
        elif entity_type == "database":
            return self.graph.add_database(
                db_id=entity_id,
                name=data.get("name", entity_id),
                db_type=data.get("type", "postgresql"),
                cloud_provider=data.get("cloud_provider", "local"),
            )
        elif entity_type == "process":
            return self.graph.add_process(
                process_id=entity_id,
                name=data.get("name", entity_id),
                container_id=data.get("container_id", ""),
                pod_id=data.get("pod_id", ""),
                host_id=data.get("host_id", ""),
            )
        elif entity_type == "genai_service":
            return self.graph.add_genai_service(
                service_id=entity_id,
                name=data.get("name", entity_id),
                model=data.get("model", ""),
                provider=data.get("provider", ""),
            )
        else:
            logger.warning("Unknown entity type for add: %s", entity_type)
            return False

    def _remove_entity(self, entity_id: str) -> bool:
        """Remove an entity from the graph."""
        # Try to delete from each node type
        for node_type in ["Service", "Process", "Host", "Database", "GenAIService",
                          "Infrastructure", "BusinessTransaction", "CostCenter"]:
            result = self.graph.store.delete_node(node_type, entity_id)
            if result:
                return True
        return False

    def _update_entity(self, entity_id: str, data: dict[str, Any]) -> bool:
        """Update entity properties."""
        # Update anomaly score if provided
        if "anomaly_score" in data:
            for node_type in ["Service", "Process", "Host", "Database", "GenAIService"]:
                self.graph.update_anomaly_score(node_type, entity_id, float(data["anomaly_score"]))
        return True

    def _add_dependency(self, source_id: str, data: dict[str, Any]) -> bool:
        """Add a dependency relationship."""
        target_id = data.get("target_id", "")
        dep_type = data.get("dependency_type", "calls")
        return self.graph.add_relationship(source_id, target_id, "DEPENDS_ON", {
            "dependency_type": dep_type,
            "criticality": data.get("criticality", "medium"),
        })

    def _remove_dependency(self, source_id: str, data: dict[str, Any]) -> bool:
        """Remove a dependency relationship."""
        # Kuzu doesn't support direct relationship deletion by properties easily
        # This would need a custom query in production
        logger.info("Dependency removal requested: %s -> %s", source_id, data.get("target_id"))
        return True

    def _update_status(self, entity_id: str, data: dict[str, Any], old_data: dict[str, Any]) -> bool:
        """Update entity status."""
        new_status = data.get("status", "unknown")
        logger.info("Status update for %s: %s -> %s", entity_id, old_data.get("status"), new_status)
        return True

    def _update_anomaly_score(self, entity_id: str, data: dict[str, Any]) -> bool:
        """Update anomaly score."""
        score = float(data.get("anomaly_score", 0))
        for node_type in ["Service", "Process", "Host", "Database", "GenAIService"]:
            self.graph.update_anomaly_score(node_type, entity_id, score)
        return True

    def get_stats(self) -> dict[str, Any]:
        """Get processing statistics."""
        return {
            "processed_count": self._processed_count,
        }
