"""
OmniWatch 2.0 — NexusStore
Component: Redis Optimizer
Layer: 4
Phase: 7
Purpose: Redis performance utilities using real Redis
Inputs: Redis operations, memory metrics
Outputs: Optimized pipelines, cache warming, memory profiling
"""

import json
import logging
import os
from typing import Any

from config import config

logger = logging.getLogger(__name__)


class RedisOptimizer:
    """Redis performance optimization utilities using real Redis."""

    def __init__(self, redis_client=None):
        if redis_client:
            self._client = redis_client
        else:
            try:
                import redis
                self._client = redis.Redis(
                    host=config.REDIS_HOST,
                    port=config.REDIS_PORT,
                    db=int(os.environ.get("REDIS_DB", 0)),
                    decode_responses=True,
                )
            except Exception as e:
                logger.warning("Redis not available: %s", e)
                self._client = None

    def pipeline_batch(self, operations: list[dict]) -> list[Any]:
        """Execute batch operations using Redis pipeline."""
        if not self._client:
            return [None] * len(operations)

        try:
            pipe = self._client.pipeline()
            for op in operations:
                op_type = op.get("type", op[0] if isinstance(op, (list, tuple)) else "")
                key = op.get("key", op[1] if isinstance(op, (list, tuple)) and len(op) > 1 else "")
                value = op.get("value", op[2] if isinstance(op, (list, tuple)) and len(op) > 2 else None)
                ttl = op.get("ttl", config.ENTITY_CACHE_TTL)

                if op_type == "set":
                    pipe.set(key, json.dumps(value) if not isinstance(value, str) else value, ex=ttl)
                elif op_type == "get":
                    pipe.get(key)
                elif op_type == "delete":
                    pipe.delete(key)

            return pipe.execute()
        except Exception as e:
            logger.error("Pipeline batch failed: %s", e)
            return [None] * len(operations)

    def cache_warming(self, hot_data: dict[str, Any], ttl: int = 600) -> int:
        """Pre-populate cache with hot data."""
        if not self._client:
            return 0

        try:
            pipe = self._client.pipeline()
            count = 0
            for key, value in hot_data.items():
                pipe.set(key, json.dumps(value) if not isinstance(value, str) else value, ex=ttl)
                count += 1
            pipe.execute()
            return count
        except Exception as e:
            logger.error("Cache warming failed: %s", e)
            return 0

    def memory_profile(self) -> dict[str, Any]:
        """Profile Redis memory usage."""
        if not self._client:
            return {"used_memory": 0, "keys_count": 0, "hit_rate": 0.0}

        try:
            info = self._client.info("memory")
            db_info = self._client.info("keyspace")
            db0 = db_info.get("db0", {})
            return {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keys_count": db0.get("keys", 0),
                "hit_rate": 0.0,
            }
        except Exception as e:
            logger.error("Memory profile failed: %s", e)
            return {"used_memory": 0, "keys_count": 0, "hit_rate": 0.0}

    def set_ttl(self, key: str, ttl_seconds: int) -> bool:
        """Set TTL on a key."""
        if not self._client:
            return False

        try:
            self._client.expire(key, ttl_seconds)
            return True
        except Exception as e:
            logger.error("Set TTL failed: %s", e)
            return False
