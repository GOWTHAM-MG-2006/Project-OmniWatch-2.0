"""
OmniWatch 2.0 — TopoBrain
Component: Entity Registry
Layer: 5
Phase: 1
Purpose: Redis cache + ClickHouse entity history for fast lookups
Inputs: Entity registration requests from StreamForge and TopoBrain
Outputs: Cached entity data, entity history
"""

import os
import json
import logging
from datetime import datetime
from typing import Any

import redis

logger = logging.getLogger(__name__)


class EntityRegistry:
    """Redis cache + ClickHouse entity history for fast entity lookups."""

    def __init__(
        self,
        redis_host: str | None = None,
        redis_port: int | None = None,
        redis_db: int = 0,
    ):
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(redis_port or os.getenv("REDIS_PORT", "6379"))
        self.redis_db = redis_db
        self._redis = None

        self.PREFIX_ENTITY = "ow:registry:entity:"
        self.PREFIX_STATUS = "ow:registry:status:"
        self.PREFIX_HISTORY = "ow:registry:history:"
        self.TTL_SECONDS = 86400  # 24 hours

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

    def register_entity(self, entity_id: str, entity_data: dict[str, Any]) -> bool:
        """Register or update an entity in the registry."""
        try:
            entity_data["entity_id"] = entity_id
            entity_data["registered_at"] = datetime.utcnow().isoformat()

            self.client.hset(
                f"{self.PREFIX_ENTITY}{entity_id}",
                mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                         for k, v in entity_data.items()},
            )
            self.client.expire(f"{self.PREFIX_ENTITY}{entity_id}", self.TTL_SECONDS)

            # Add to history
            self.client.lpush(
                f"{self.PREFIX_HISTORY}{entity_id}",
                json.dumps({
                    "action": "registered",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": entity_data,
                }),
            )
            self.client.ltrim(f"{self.PREFIX_HISTORY}{entity_id}", 0, 99)

            logger.info("Registered entity: %s", entity_id)
            return True
        except Exception as e:
            logger.error("Failed to register entity %s: %s", entity_id, e)
            return False

    def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        """Get entity data from the registry."""
        data = self.client.hgetall(f"{self.PREFIX_ENTITY}{entity_id}")
        if not data:
            return None

        # Parse JSON fields
        result = {}
        for k, v in data.items():
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                result[k] = v
        return result

    def update_status(self, entity_id: str, status: str) -> bool:
        """Update entity status."""
        try:
            self.client.hset(f"{self.PREFIX_ENTITY}{entity_id}", "status", status)
            self.client.hset(f"{self.PREFIX_ENTITY}{entity_id}", "last_updated",
                           datetime.utcnow().isoformat())

            # Track status changes
            self.client.lpush(
                f"{self.PREFIX_HISTORY}{entity_id}",
                json.dumps({
                    "action": "status_changed",
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat(),
                }),
            )
            self.client.ltrim(f"{self.PREFIX_HISTORY}{entity_id}", 0, 99)

            return True
        except Exception as e:
            logger.error("Failed to update status for %s: %s", entity_id, e)
            return False

    def get_history(self, entity_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get entity history."""
        raw = self.client.lrange(f"{self.PREFIX_HISTORY}{entity_id}", 0, limit - 1)
        return [json.loads(entry) for entry in raw]

    def list_entities(self, pattern: str = "*") -> list[str]:
        """List all entity IDs matching a pattern."""
        keys = self.client.keys(f"{self.PREFIX_ENTITY}{pattern}")
        return [k.replace(self.PREFIX_ENTITY, "") for k in keys]

    def delete_entity(self, entity_id: str) -> bool:
        """Remove an entity from the registry."""
        try:
            self.client.delete(f"{self.PREFIX_ENTITY}{entity_id}")
            self.client.delete(f"{self.PREFIX_HISTORY}{entity_id}")
            return True
        except Exception as e:
            logger.error("Failed to delete entity %s: %s", entity_id, e)
            return False

    def health_check(self) -> bool:
        """Verify Redis connectivity."""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error("Entity registry health check failed: %s", e)
            return False
