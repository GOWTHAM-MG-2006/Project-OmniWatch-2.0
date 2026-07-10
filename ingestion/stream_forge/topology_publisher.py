"""
OmniWatch 2.0 — StreamForge
Component: Topology Publisher
Layer: 3
Phase: 1
Purpose: Publishes topology deltas to TopoBrain via Kafka
Inputs: Entity resolution events, dependency discoveries
Outputs: Topology delta events on omniwatch.topology.deltas topic
"""

import os
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Topology change types
CHANGE_TYPES = {
    "ENTITY_ADDED": "A new entity was discovered",
    "ENTITY_REMOVED": "An entity disappeared",
    "ENTITY_UPDATED": "Entity metadata changed",
    "DEPENDENCY_ADDED": "A new dependency was discovered",
    "DEPENDENCY_REMOVED": "A dependency no longer exists",
    "STATUS_CHANGED": "Entity status changed",
    "ANOMALY_SCORE_UPDATED": "Entity anomaly score changed",
}


class TopologyPublisher:
    """Publishes topology deltas to TopoBrain via Kafka."""

    def __init__(self, kafka_producer=None):
        self._producer = kafka_producer
        self._pending_deltas: list[dict[str, Any]] = []

    def publish_delta(
        self,
        entity_id: str,
        change_type: str,
        entity_data: dict[str, Any] | None = None,
        old_data: dict[str, Any] | None = None,
    ) -> bool:
        """Publish a topology delta event."""
        if change_type not in CHANGE_TYPES:
            logger.warning("Unknown change type: %s", change_type)

        delta = {
            "entity_id": entity_id,
            "change_type": change_type,
            "change_description": CHANGE_TYPES.get(change_type, "Unknown change"),
            "entity_data": entity_data or {},
            "old_data": old_data or {},
            "timestamp": time.time(),
            "source": "streamforge",
        }

        return self.emit_to_topic(delta)

    def publish_entity_added(self, entity_id: str, entity_data: dict[str, Any]) -> bool:
        """Publish an entity added event."""
        return self.publish_delta(entity_id, "ENTITY_ADDED", entity_data=entity_data)

    def publish_entity_removed(self, entity_id: str) -> bool:
        """Publish an entity removed event."""
        return self.publish_delta(entity_id, "ENTITY_REMOVED")

    def publish_dependency_added(
        self,
        source_id: str,
        target_id: str,
        dependency_type: str = "calls",
    ) -> bool:
        """Publish a dependency added event."""
        delta = {
            "entity_id": source_id,
            "change_type": "DEPENDENCY_ADDED",
            "change_description": f"Dependency added: {source_id} -> {target_id}",
            "entity_data": {
                "source_id": source_id,
                "target_id": target_id,
                "dependency_type": dependency_type,
            },
            "timestamp": time.time(),
            "source": "streamforge",
        }
        return self.emit_to_topic(delta)

    def publish_status_changed(
        self,
        entity_id: str,
        old_status: str,
        new_status: str,
    ) -> bool:
        """Publish a status changed event."""
        return self.publish_delta(
            entity_id,
            "STATUS_CHANGED",
            entity_data={"status": new_status},
            old_data={"status": old_status},
        )

    def publish_anomaly_score_updated(
        self,
        entity_id: str,
        old_score: float,
        new_score: float,
    ) -> bool:
        """Publish an anomaly score update."""
        return self.publish_delta(
            entity_id,
            "ANOMALY_SCORE_UPDATED",
            entity_data={"anomaly_score": new_score},
            old_data={"anomaly_score": old_score},
        )

    def emit_to_topic(self, delta: dict[str, Any]) -> bool:
        """Emit a topology delta to the Kafka topic."""
        topic = "omniwatch.topology.deltas"
        key = delta.get("entity_id", "unknown")

        # Buffer if no producer available
        if self._producer is None:
            self._pending_deltas.append(delta)
            logger.debug("Buffered topology delta (no producer): %s", key)
            return True

        try:
            return self._producer.produce(topic, key, delta)
        except Exception as e:
            logger.error("Failed to emit topology delta: %s", e)
            self._pending_deltas.append(delta)
            return False

    def flush_pending(self) -> int:
        """Flush buffered deltas when a producer becomes available."""
        if self._producer is None or not self._pending_deltas:
            return 0

        count = 0
        for delta in self._pending_deltas:
            if self.emit_to_topic(delta):
                count += 1

        self._pending_deltas.clear()
        return count

    def get_pending_count(self) -> int:
        """Get count of pending deltas."""
        return len(self._pending_deltas)
