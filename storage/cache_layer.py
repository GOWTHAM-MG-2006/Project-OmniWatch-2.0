"""
OmniWatch 2.0 — NexusStore
Component: Cache Layer
Layer: 4
Phase: 7
Purpose: Multi-level caching system
Inputs: Query results, cache configuration
Outputs: Cached data with TTL and invalidation
"""

import time
import logging
from typing import Any

logger = logging.getLogger(__name__)


class CacheLayer:
    """Multi-level caching system."""

    def __init__(self):
        self._l1_cache: dict[str, dict] = {}
        self._hits = 0
        self._misses = 0

    def set(self, key: str, value: Any, ttl: int = 30) -> bool:
        """Set value in L1 cache with TTL."""
        self._l1_cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
        }
        return True

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        entry = self._l1_cache.get(key)
        if entry:
            if time.time() < entry["expires_at"]:
                self._hits += 1
                return entry["value"]
            else:
                del self._l1_cache[key]
        self._misses += 1
        return None

    def invalidate(self, key: str) -> bool:
        """Invalidate a cache entry."""
        self._l1_cache.pop(key, None)
        return True

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        count = 0
        keys_to_delete = [k for k in self._l1_cache if pattern in k]
        for key in keys_to_delete:
            del self._l1_cache[key]
            count += 1
        return count

    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "l1_size": len(self._l1_cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.get_hit_rate(),
        }
