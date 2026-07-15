"""
OmniWatch 2.0 — StreamForge
Component: Entity Resolution
Layer: 3
Phase: 1
Purpose: Maps volatile telemetry IDs (pod UIDs, container IDs, IPs) to stable entities
Inputs: Raw telemetry with volatile identifiers
Outputs: Stabilized entity IDs for consistent topology and RCA
"""

import os
import json
import logging
import hashlib
from typing import Any
from datetime import datetime

import redis

from config import config

logger = logging.getLogger(__name__)

# Entity type hierarchy for resolution priority
ENTITY_TYPE_PRIORITY = {
    "service": 1,
    "database": 2,
    "host": 3,
    "container": 4,
    "pod": 5,
    "process": 6,
    "ip": 7,
}


class EntityResolution:
    """Redis-backed entity resolution for stabilizing volatile telemetry IDs."""

    def __init__(
        self,
        redis_host: str | None = None,
        redis_port: int | None = None,
        redis_db: int = 0,
    ):
        self.redis_host = redis_host or config.REDIS_HOST
        self.redis_port = int(redis_port or config.REDIS_PORT)
        self.redis_db = redis_db
        self._redis = None

        # Key prefixes
        self.PREFIX_VOLATILE = "ow:entity:volatile:"
        self.PREFIX_STABLE = "ow:entity:stable:"
        self.PREFIX_HISTORY = "ow:entity:history:"
        self.TTL_SECONDS = config.ENTITY_RESOLUTION_TTL

    @property
    def client(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
            )
        return self._redis

    def resolve_entity(
        self,
        volatile_id: str,
        entity_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Resolve a volatile ID to a stable entity ID.

        If a mapping exists, return the stable ID.
        If not, create a new stable ID and store the mapping.
        """
        # Check if we already have a mapping
        stable_id = self.get_stable_id(volatile_id)
        if stable_id:
            # Update last seen
            self._update_last_seen(stable_id)
            # Merge new metadata if provided
            if metadata:
                self._merge_metadata(stable_id, metadata)
            return stable_id

        # Generate a stable ID from the volatile ID + entity type
        stable_id = self._generate_stable_id(volatile_id, entity_type)

        # Store the mapping
        self.client.setex(
            f"{self.PREFIX_VOLATILE}{volatile_id}",
            self.TTL_SECONDS,
            stable_id,
        )

        # Store entity metadata
        entity_data = {
            "stable_id": stable_id,
            "entity_type": entity_type,
            "volatile_id": volatile_id,
            "first_seen": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat(),
            "metadata": json.dumps(metadata or {}),
        }
        self.client.hset(f"{self.PREFIX_STABLE}{stable_id}", mapping=entity_data)
        self.client.expire(f"{self.PREFIX_STABLE}{stable_id}", self.TTL_SECONDS)

        # Add to history
        self.client.lpush(
            f"{self.PREFIX_HISTORY}{stable_id}",
            json.dumps({
                "volatile_id": volatile_id,
                "timestamp": datetime.utcnow().isoformat(),
                "entity_type": entity_type,
            }),
        )
        self.client.ltrim(f"{self.PREFIX_HISTORY}{stable_id}", 0, 99)

        logger.info("Resolved new entity: %s -> %s (%s)", volatile_id, stable_id, entity_type)
        return stable_id

    def get_stable_id(self, volatile_id: str) -> str | None:
        """Get the stable ID for a volatile ID, or None if not mapped."""
        return self.client.get(f"{self.PREFIX_VOLATILE}{volatile_id}")

    def get_entity(self, stable_id: str) -> dict[str, Any] | None:
        """Get full entity data by stable ID."""
        data = self.client.hgetall(f"{self.PREFIX_STABLE}{stable_id}")
        if not data:
            return None
        data["metadata"] = json.loads(data.get("metadata", "{}"))
        return data

    def get_history(self, stable_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get the resolution history for an entity."""
        raw = self.client.lrange(f"{self.PREFIX_HISTORY}{stable_id}", 0, limit - 1)
        return [json.loads(entry) for entry in raw]

    def _generate_stable_id(self, volatile_id: str, entity_type: str) -> str:
        """Generate a deterministic stable ID."""
        hash_input = f"{entity_type}:{volatile_id}"
        hash_val = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
        return f"ow-{entity_type[:3]}-{hash_val}"

    def _update_last_seen(self, stable_id: str):
        """Update the last_seen timestamp."""
        self.client.hset(
            f"{self.PREFIX_STABLE}{stable_id}",
            "last_seen",
            datetime.utcnow().isoformat(),
        )

    def _merge_metadata(self, stable_id: str, new_metadata: dict[str, Any]):
        """Merge new metadata with existing metadata."""
        existing = self.client.hget(f"{self.PREFIX_STABLE}{stable_id}", "metadata")
        existing_meta = json.loads(existing) if existing else {}
        existing_meta.update(new_metadata)
        self.client.hset(
            f"{self.PREFIX_STABLE}{stable_id}",
            "metadata",
            json.dumps(existing_meta),
        )

    def bulk_resolve(
        self,
        items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Resolve a batch of items, each with volatile_id and entity_type.

        Returns the input list with 'stable_id' added to each item.
        """
        resolved = []
        for item in items:
            volatile_id = item.get("entity_id") or item.get("volatile_id")
            entity_type = item.get("entity_type", "unknown")
            if volatile_id:
                stable_id = self.resolve_entity(volatile_id, entity_type, item)
                item["stable_id"] = stable_id
            resolved.append(item)
        return resolved

    def health_check(self) -> bool:
        """Verify Redis connectivity."""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error("Entity resolution health check failed: %s", e)
            return False
