"""
OmniWatch 2.0 — SimulaX
Component: Digital Twin
Layer: 8
Phase: 3
Purpose: Continuously updated model of production environment for simulation
Inputs: NexusStore metrics + TopoBrain topology + NeuroEngine models
Outputs: Digital twin state in Redis (entity states, resource utilization, dependency graph)
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logger.info("redis-py not installed — DigitalTwin will use in-memory fallback")


class DigitalTwin:
    """Continuously updated model of the production environment.

    Maintains entity states, resource utilization, and dependency graph
    in Redis for low-latency simulation queries.
    """

    def __init__(
        self,
        redis_host: str | None = None,
        redis_port: int | None = None,
        redis_db: int = 2,
    ):
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(redis_port or os.getenv("REDIS_PORT", "6379"))
        self.redis_db = redis_db
        self._redis = None
        self._memory_store: dict[str, str] = {}
        self._prefix = "ow:twin:"

    @property
    def conn(self):
        if self._redis is None and HAS_REDIS:
            try:
                self._redis = redis.Redis(
                    host=self.redis_host, port=self.redis_port,
                    db=self.redis_db, decode_responses=True,
                )
                self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    def _store_set(self, key: str, value: str) -> None:
        if self.conn:
            self.conn.set(key, value)
        else:
            self._memory_store[key] = value

    def _store_get(self, key: str) -> str | None:
        if self.conn:
            return self.conn.get(key)
        return self._memory_store.get(key)

    def _store_keys(self, pattern: str) -> list[str]:
        if self.conn:
            return self.conn.keys(pattern)
        import fnmatch
        return [k for k in self._memory_store if fnmatch.fnmatch(k, pattern)]

    def _store_delete(self, *keys: str) -> None:
        if self.conn:
            self.conn.delete(*keys)
        else:
            for k in keys:
                self._memory_store.pop(k, None)

    def _key(self, entity_id: str) -> str:
        return f"{self._prefix}{entity_id}"

    def update_entity(
        self,
        entity_id: str,
        entity_type: str,
        state: dict[str, Any],
    ) -> None:
        """Update entity state in the digital twin."""
        payload = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "state": state,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._store_set(self._key(entity_id), json.dumps(payload, default=str))
        logger.debug("Updated twin entity: %s", entity_id)

    def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        """Get current state of an entity."""
        raw = self._store_get(self._key(entity_id))
        if raw is None:
            return None
        return json.loads(raw)

    def get_all_entities(self) -> list[dict[str, Any]]:
        """Get all entities in the digital twin."""
        keys = self._store_keys(f"{self._prefix}*")
        entities = []
        for key in keys:
            raw = self._store_get(key)
            if raw:
                entities.append(json.loads(raw))
        return entities

    def update_resource_utilization(
        self,
        entity_id: str,
        cpu_percent: float = 0.0,
        memory_percent: float = 0.0,
        disk_percent: float = 0.0,
        network_mbps: float = 0.0,
    ) -> None:
        """Update resource utilization metrics for an entity."""
        entity = self.get_entity(entity_id) or {"entity_id": entity_id, "entity_type": "unknown", "state": {}}
        entity["state"]["resources"] = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "network_mbps": network_mbps,
        }
        self.update_entity(entity_id, entity.get("entity_type", "unknown"), entity["state"])

    def update_dependency_graph(self, edges: list[dict[str, str]]) -> None:
        """Update the dependency graph (list of {from, to, type} edges)."""
        self._store_set(f"{self._prefix}dep_graph", json.dumps(edges))

    def get_dependency_graph(self) -> list[dict[str, str]]:
        """Get the current dependency graph."""
        raw = self._store_get(f"{self._prefix}dep_graph")
        if raw is None:
            return []
        return json.loads(raw)

    def get_downstream(self, entity_id: str) -> list[str]:
        """Get all downstream entities (entities that depend on this one)."""
        graph = self.get_dependency_graph()
        return [e["to"] for e in graph if e["from"] == entity_id]

    def get_upstream(self, entity_id: str) -> list[str]:
        """Get all upstream entities (entities this one depends on)."""
        graph = self.get_dependency_graph()
        return [e["from"] for e in graph if e["to"] == entity_id]

    def clear(self) -> None:
        """Clear all digital twin state."""
        keys = self._store_keys(f"{self._prefix}*")
        if keys:
            self._store_delete(*keys)
        logger.info("Digital twin state cleared")
