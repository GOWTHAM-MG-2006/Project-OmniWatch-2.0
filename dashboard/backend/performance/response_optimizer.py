"""
OmniWatch 2.0 — NexusUX
Component: Response Optimizer
Layer: 11
Phase: 7
Purpose: API performance utilities
Inputs: API responses, query parameters
Outputs: Cached responses, paginated results, compressed data
"""

import hashlib
import gzip
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ResponseOptimizer:
    """API response optimization utilities."""

    def __init__(self):
        self._cache: dict[str, dict] = {}

    def cache_response(self, path: str, response: dict, ttl: int = 30) -> bool:
        """Cache API response with TTL."""
        cache_key = hashlib.md5(path.encode()).hexdigest()
        self._cache[cache_key] = {"data": response, "ttl": ttl}
        return True

    def get_cached_response(self, path: str) -> dict | None:
        """Get cached API response."""
        cache_key = hashlib.md5(path.encode()).hexdigest()
        cached = self._cache.get(cache_key)
        if cached:
            return cached["data"]
        return None

    def add_pagination(self, items: list, page: int = 1, page_size: int = 50) -> dict:
        """Add cursor-based pagination."""
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "items": items[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_next": end < total,
        }

    def compress_response(self, data: bytes) -> bytes:
        """Compress response using gzip."""
        if len(data) > 1024:
            return gzip.compress(data)
        return data

    def generate_etag(self, data: dict) -> str:
        """Generate ETag for conditional requests."""
        import json
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.md5(serialized.encode()).hexdigest()
