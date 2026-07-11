"""
OmniWatch 2.0 — NexusStore
Component: Cache Layer
Layer: 4
Phase: 7
Purpose: Multi-level caching (L1 in-memory + L2 Redis) with TTL,
         pattern invalidation, hit-rate monitoring, and L1 eviction
Inputs: Query results, cache configuration
Outputs: Cached data with TTL and invalidation
Technology: Python, threading, redis
"""

import fnmatch
import logging
import os
import threading
import time
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)

try:
    import redis as _redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class L1Cache:
    """In-memory LRU dict with per-entry TTL and configurable max size."""

    def __init__(self, max_size: int = 1024, default_ttl: int = 60):
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._data: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                self._misses += 1
                return None
            if time.monotonic() > entry["expires_at"]:
                del self._data[key]
                self._misses += 1
                return None
            self._data.move_to_end(key)
            self._hits += 1
            return entry["value"]

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        with self._lock:
            if ttl is None:
                ttl = self._default_ttl
            if key in self._data:
                del self._data[key]
            elif len(self._data) >= self._max_size:
                self._data.popitem(last=False)
                self._evictions += 1
            self._data[key] = {
                "value": value,
                "expires_at": time.monotonic() + ttl,
                "set_at": time.monotonic(),
            }

    def invalidate(self, key: str) -> bool:
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        count = 0
        with self._lock:
            keys_to_remove = [k for k in list(self._data.keys()) if fnmatch.fnmatch(k, pattern)]
            for key in keys_to_remove:
                del self._data[key]
                count += 1
        return count

    def clear(self) -> int:
        with self._lock:
            count = len(self._data)
            self._data.clear()
            return count

    def get_stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        return {
            "size": len(self._data),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total > 0 else 0.0,
            "evictions": self._evictions,
        }


class L2Cache:
    """Redis-backed distributed cache with TTL."""

    def __init__(self, host: str = "localhost", port: int = 6379,
                 db: int = 0, default_ttl: int = 120,
                 prefix: str = "omniwatch:cache:",
                 password: str | None = None):
        self._prefix = prefix
        self._default_ttl = default_ttl
        self._client: Any = None
        self._available = False
        self._hits = 0
        self._misses = 0
        if HAS_REDIS:
            try:
                self._client = _redis.Redis(
                    host=host, port=port, db=db, password=password,
                    socket_connect_timeout=3, socket_timeout=5,
                    decode_responses=True,
                )
                self._client.ping()
                self._available = True
                logger.info("L2 Redis cache connected at %s:%d", host, port)
            except Exception as exc:
                logger.warning("L2 Redis cache unavailable: %s", exc)

    def _key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Any | None:
        if not self._available:
            self._misses += 1
            return None
        try:
            raw = self._client.get(self._key(key))
            if raw is None:
                self._misses += 1
                return None
            import json
            self._hits += 1
            return json.loads(raw)
        except Exception:
            self._misses += 1
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        if not self._available:
            return False
        try:
            import json
            ttl = ttl or self._default_ttl
            self._client.setex(self._key(key), ttl, json.dumps(value))
            return True
        except Exception as exc:
            logger.warning("L2 cache set failed for key %s: %s", key, exc)
            return False

    def invalidate(self, key: str) -> bool:
        if not self._available:
            return False
        try:
            return bool(self._client.delete(self._key(key)))
        except Exception:
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        if not self._available:
            return 0
        try:
            full_pattern = self._key(pattern)
            count = 0
            cursor = 0
            while True:
                cursor, keys = self._client.scan(cursor=cursor, match=full_pattern, count=200)
                if keys:
                    count += self._client.delete(*keys)
                if cursor == 0:
                    break
            return count
        except Exception:
            return 0

    def get_stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        info: dict[str, Any] = {
            "available": self._available,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total > 0 else 0.0,
        }
        if self._available:
            try:
                info["keys"] = len(self._client.keys(f"{self._prefix}*"))
                info["used_memory_human"] = self._client.info("memory").get("used_memory_human", "N/A")
            except Exception:
                pass
        return info


class CacheLayer:
    """Multi-level cache: L1 (in-memory LRU) + L2 (Redis)."""

    def __init__(self, l1_max_size: int = 1024, l1_ttl: int = 60,
                 l2_ttl: int = 120, l2_enabled: bool = True):
        self._l1 = L1Cache(max_size=l1_max_size, default_ttl=l1_ttl)
        self._l2: L2Cache | None = None
        if l2_enabled:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_pw = os.getenv("REDIS_PASSWORD") or None
            self._l2 = L2Cache(host=redis_host, port=redis_port,
                               default_ttl=l2_ttl, password=redis_pw)

    def get(self, key: str) -> Any | None:
        """Get value from cache (L1 first, then L2)."""
        val = self._l1.get(key)
        if val is not None:
            return val
        if self._l2:
            val = self._l2.get(key)
            if val is not None:
                # Promote to L1
                self._l1.set(key, val)
                return val
        return None

    def set(self, key: str, value: Any, ttl: int | None = None,
            l2_ttl: int | None = None) -> bool:
        """Set value in both L1 and L2."""
        self._l1.set(key, value, ttl=ttl)
        if self._l2:
            return self._l2.set(key, value, ttl=l2_ttl or (ttl * 2 if ttl else None))
        return True

    def invalidate(self, key: str) -> bool:
        """Invalidate a key in both levels."""
        l1_removed = self._l1.invalidate(key)
        l2_removed = self._l2.invalidate(key) if self._l2 else False
        return l1_removed or l2_removed

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a glob pattern in both levels."""
        count = self._l1.invalidate_pattern(pattern)
        if self._l2:
            count += self._l2.invalidate_pattern(pattern)
        return count

    def clear(self) -> int:
        """Clear all cached data."""
        count = self._l1.clear()
        return count

    def get_hit_rate(self) -> float:
        """Get overall L1 hit rate."""
        stats = self._l1.get_stats()
        return stats["hit_rate"]

    def get_stats(self) -> dict[str, Any]:
        """Get combined cache statistics."""
        stats: dict[str, Any] = {"l1": self._l1.get_stats()}
        if self._l2:
            stats["l2"] = self._l2.get_stats()
        else:
            stats["l2"] = {"available": False}
        return stats
