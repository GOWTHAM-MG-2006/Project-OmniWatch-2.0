"""
OmniWatch 2.0 — StreamForge
Component: Stream Optimizer
Layer: 3
Phase: 7
Purpose: StreamForge performance utilities
Inputs: Entity data, PII patterns
Outputs: Batch resolution, async PII detection
"""

import re
import logging
from typing import Any

from config import config

logger = logging.getLogger(__name__)

PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
}


class StreamOptimizer:
    """StreamForge performance optimization utilities."""

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._entity_cache: dict[str, dict] = {}
        self._compiled_patterns = {k: re.compile(v) for k, v in PII_PATTERNS.items()}

    def batch_entity_resolution(self, entities: list[dict]) -> list[dict]:
        """Batch entity resolution using Redis cache with deterministic ID generation."""
        import hashlib
        results = []
        for entity in entities:
            entity_id = entity.get("id", "")
            entity_type = entity.get("type", "unknown")
            metadata = entity.get("metadata", {})

            cache_key = f"entity:{entity_id}"
            cached = None

            if self._redis:
                try:
                    cached_raw = self._redis.get(cache_key)
                    if cached_raw:
                        import json
                        cached = json.loads(cached_raw)
                except Exception:
                    pass

            if cached:
                results.append(cached)
            else:
                stable_id = hashlib.sha256(f"{entity_type}:{entity_id}".encode()).hexdigest()[:16]
                resolved = {
                    "resolved_id": stable_id,
                    "original_id": entity_id,
                    "entity_type": entity_type,
                    "stable": True,
                    "metadata": metadata,
                }
                self._entity_cache[entity_id] = resolved
                if self._redis:
                    try:
                        import json
                        self._redis.setex(cache_key, config.ENTITY_CACHE_TTL, json.dumps(resolved))
                    except Exception:
                        pass
                results.append(resolved)
        return results

    def async_pii_detection(self, text: str) -> dict[str, list[str]]:
        """Detect PII in text using pre-compiled patterns."""
        detections = {}
        for pii_type, pattern in self._compiled_patterns.items():
            matches = pattern.findall(text)
            if matches:
                detections[pii_type] = matches
        return detections

    def sample_pii_detection(self, text: str, sample_rate: float = 0.1) -> dict[str, list[str]] | None:
        """Sample PII detection for high-volume streams."""
        import random
        if random.random() < sample_rate:
            return self.async_pii_detection(text)
        return None
