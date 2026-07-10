"""
OmniWatch 2.0 — StreamForge
Component: Enrichment Engine
Layer: 3
Phase: 1
Purpose: Semantic normalization and entity enrichment for telemetry data
Inputs: Raw telemetry events
Outputs: Enriched events with normalized fields and topology context
"""

import os
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Metric name normalization map
METRIC_NORMALIZATION = {
    "cpu.usage": "cpu_usage_pct",
    "cpu.utilization": "cpu_usage_pct",
    "mem.usage": "memory_usage_pct",
    "mem.utilization": "memory_usage_pct",
    "memory.usage": "memory_usage_pct",
    "disk.io.read": "disk_read_bytes",
    "disk.io.write": "disk_write_bytes",
    "net.rx": "network_rx_bytes",
    "net.tx": "network_tx_bytes",
    "http.request.duration": "http_request_duration_ms",
    "http.request.count": "http_request_count",
    "grpc.request.duration": "grpc_request_duration_ms",
    "db.query.duration": "db_query_duration_ms",
    "db.connections.active": "db_active_connections",
    "container.cpu": "container_cpu_usage_pct",
    "container.memory": "container_memory_usage_pct",
    "pod.restart": "pod_restart_count",
    "llm.token.input": "llm_input_tokens",
    "llm.token.output": "llm_output_tokens",
    "llm.latency": "llm_request_latency_ms",
    "llm.cost": "llm_cost_usd",
}

# Entity type normalization
ENTITY_TYPE_NORMALIZATION = {
    "pod": "container",
    "deployment": "service",
    "replicaset": "service",
    "daemonset": "service",
    "statefulset": "service",
    "node": "host",
    "vm": "host",
    "rds": "database",
    "mysql": "database",
    "postgresql": "database",
    "postgres": "database",
    "redis-cache": "database",
}


class EnrichmentEngine:
    """Semantic normalization and entity enrichment for telemetry."""

    def __init__(self):
        self._entity_cache: dict[str, dict[str, Any]] = {}

    def enrich(self, event: dict[str, Any]) -> dict[str, Any]:
        """Enrich a raw telemetry event."""
        enriched = dict(event)

        # Normalize metric name
        if "metric_name" in enriched:
            raw_name = enriched["metric_name"]
            enriched["metric_name"] = METRIC_NORMALIZATION.get(raw_name, raw_name)

        # Normalize entity type
        if "entity_type" in enriched:
            raw_type = enriched["entity_type"]
            enriched["entity_type"] = ENTITY_TYPE_NORMALIZATION.get(raw_type, raw_type)

        # Ensure stable_id from entity resolution
        if "stable_id" not in enriched and "entity_id" in enriched:
            enriched["stable_id"] = enriched["entity_id"]

        # Add enrichment metadata
        enriched["enriched_at"] = __import__("datetime").datetime.utcnow().isoformat()
        enriched["enrichment_version"] = "1.0"

        # Add topology context if available
        if "entity_id" in enriched:
            entity_context = self._get_entity_context(enriched["entity_id"])
            if entity_context:
                enriched["topology_context"] = entity_context

        return enriched

    def normalize_entity(self, entity: dict[str, Any]) -> dict[str, Any]:
        """Normalize entity fields for consistent storage."""
        normalized = dict(entity)

        # Normalize entity type
        if "type" in normalized:
            raw_type = normalized["type"]
            normalized["type"] = ENTITY_TYPE_NORMALIZATION.get(raw_type, raw_type)

        # Normalize status values
        if "status" in normalized:
            status_map = {
                "running": "healthy",
                "active": "healthy",
                "up": "healthy",
                "stopped": "unhealthy",
                "failed": "unhealthy",
                "down": "unhealthy",
                "degraded": "degraded",
            }
            normalized["status"] = status_map.get(
                normalized["status"].lower(), normalized["status"]
            )

        return normalized

    def add_topology_context(
        self,
        event: dict[str, Any],
        dependencies: list[str] | None = None,
        dependents: list[str] | None = None,
    ) -> dict[str, Any]:
        """Add topology context to an event."""
        enriched = dict(event)
        enriched["topology_context"] = {
            "depends_on": dependencies or [],
            "depended_by": dependents or [],
        }
        return enriched

    def _get_entity_context(self, entity_id: str) -> dict[str, Any] | None:
        """Get cached entity context."""
        return self._entity_cache.get(entity_id)

    def update_entity_cache(self, entity_id: str, context: dict[str, Any]):
        """Update the entity context cache."""
        self._entity_cache[entity_id] = context

    def clear_cache(self):
        """Clear the entity cache."""
        self._entity_cache.clear()
