"""
OmniWatch 2.0 — NexusStore
Component: Query Optimizer
Layer: 4
Phase: 7
Purpose: Analyze ClickHouse query performance and suggest optimizations
Inputs: ClickHouse system.query_log
Outputs: Slow query analysis, index suggestions
"""

import hashlib
import logging
import os
from typing import Any

from config import config

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """ClickHouse query performance analyzer."""

    def __init__(self, clickhouse_client=None):
        self._client = clickhouse_client
        self._cache: dict[str, dict] = {}

    @property
    def client(self):
        if self._client is None:
            try:
                import clickhouse_connect
                self._client = clickhouse_connect.get_client(
                    host=config.CLICKHOUSE_HOST,
                    port=config.CLICKHOUSE_PORT,
                    database="omniwatch",
                )
            except Exception as e:
                logger.warning("ClickHouse not available for query optimization: %s", e)
                self._client = None
        return self._client

    def analyze_slow_queries(self, threshold_ms: float = 1000) -> list[dict]:
        """Identify queries slower than threshold from system.query_log."""
        if not self.client:
            return []

        try:
            query = """
                SELECT
                    query,
                    query_duration_ms,
                    read_rows,
                    read_bytes
                FROM system.query_log
                WHERE type = 'QueryFinish'
                  AND query_duration_ms > {threshold:Float64}
                  AND event_time >= now() - INTERVAL 24 hour
                ORDER BY query_duration_ms DESC
                LIMIT 20
            """
            result = self.client.query(query, parameters={"threshold": threshold})
            return [
                {"query_pattern": row[0][:200], "avg_ms": row[1], "count": row[2]}
                for row in result.result_rows
            ]
        except Exception as e:
            logger.warning("Failed to analyze slow queries: %s", e)
            return []

    def suggest_indexes(self) -> list[dict]:
        """Recommend index additions based on query patterns."""
        if not self.client:
            return []

        try:
            query = """
                SELECT
                    query,
                    read_rows,
                    result_rows,
                    CASE WHEN result_rows > 0
                         THEN read_rows / result_rows
                         ELSE 0 END as scan_ratio
                FROM system.query_log
                WHERE type = 'QueryFinish'
                  AND event_time >= now() - INTERVAL 24 hour
                ORDER BY scan_ratio DESC
                LIMIT 10
            """
            result = self.client.query(query)
            suggestions = []
            for row in result.result_rows:
                if row[3] > 100:
                    suggestions.append({
                        "table": "unknown",
                        "columns": [],
                        "reason": f"High scan ratio ({row[3]}:1) — consider adding an index or partition key",
                    })
            return suggestions
        except Exception as e:
            logger.warning("Failed to suggest indexes: %s", e)
            return []

    def cache_query_result(self, query_key: str, result: list, ttl: int = 30) -> bool:
        """Cache query result with TTL."""
        cache_key = hashlib.md5(query_key.encode()).hexdigest()
        self._cache[cache_key] = {"data": result, "ttl": ttl}
        return True

    def get_cached_result(self, query_key: str) -> list | None:
        """Get cached query result if not expired."""
        cache_key = hashlib.md5(query_key.encode()).hexdigest()
        cached = self._cache.get(cache_key)
        if cached:
            return cached["data"]
        return None

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cached results matching pattern."""
        keys_to_delete = [k for k in self._cache if pattern in k]
        for key in keys_to_delete:
            del self._cache[key]
        return len(keys_to_delete)
