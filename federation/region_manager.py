"""
OmniWatch 2.0 — Federation
Component: Region Manager
Layer: Enterprise (Phase 6)
Purpose: Manages multiple OmniWatch regions — registration, health monitoring, and querying
Inputs: Region registration requests, health check responses
Outputs: Region status updates, healthy region lists
"""

import os
import re
import json
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import clickhouse_connect
import redis
import requests

ALLOWED_HOSTS = re.compile(r'^(localhost|127\.0\.0\.1|[\w\-]+\.omniwatch\.io)$')
BLOCKED_NETWORKS = re.compile(r'^(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|169\.254\.)')


def validate_endpoint_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname or ""
        if BLOCKED_NETWORKS.match(hostname):
            return False
        if not ALLOWED_HOSTS.match(hostname):
            return False
        return True
    except Exception:
        return False

logger = logging.getLogger(__name__)


class RegionManager:
    """Manages multi-region federation — registration, health checks, and region queries."""

    HEALTH_CHECK_TIMEOUT = 10  # seconds

    def __init__(
        self,
        clickhouse_host: str | None = None,
        clickhouse_port: int | None = None,
        redis_host: str | None = None,
        redis_port: int | None = None,
    ):
        self.ch_host = clickhouse_host or os.getenv("CLICKHOUSE_HOST", "localhost")
        self.ch_port = int(clickhouse_port or os.getenv("CLICKHOUSE_PORT", "9000"))
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(redis_port or os.getenv("REDIS_PORT", "6379"))
        self._ch_client = None
        self._redis = None

    @property
    def ch(self):
        if self._ch_client is None:
            self._ch_client = clickhouse_connect.get_client(
                host=self.ch_host, port=self.ch_port
            )
        return self._ch_client

    @property
    def cache(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
            )
        return self._redis

    def register_region(
        self,
        region_id: str,
        endpoint: str,
        display_name: str,
        metadata: str = "{}",
    ) -> dict[str, Any]:
        """Register a new region in the federation.

        Args:
            region_id: Unique region identifier (e.g. "us-east-1").
            endpoint: Region's OmniWatch API endpoint URL.
            display_name: Human-readable region name.
            metadata: JSON string with extra metadata.

        Returns:
            Registration confirmation dict.
        """
        if not validate_endpoint_url(endpoint):
            raise ValueError(f"Invalid or blocked endpoint URL: {endpoint}")
        now = datetime.now(timezone.utc)
        row = {
            "region_id": region_id,
            "endpoint": endpoint,
            "display_name": display_name,
            "status": "healthy",
            "last_health_check": now,
            "created_at": now,
            "metadata": metadata,
        }

        self.ch.insert(
            "omniwatch.regions",
            [[
                row["region_id"],
                row["endpoint"],
                row["display_name"],
                row["status"],
                row["last_health_check"],
                row["created_at"],
                row["metadata"],
            ]],
            column_names=[
                "region_id", "endpoint", "display_name", "status",
                "last_health_check", "created_at", "metadata",
            ],
        )

        logger.info("Registered region: %s (%s)", region_id, endpoint)
        return {"region_id": region_id, "status": "registered"}

    def health_check(self, region_id: str) -> dict[str, Any]:
        """Check health of a single region and update its status.

        Args:
            region_id: The region to check.

        Returns:
            Dict with region_id, status, and checked_at timestamp.
        """
        now = datetime.now(timezone.utc)
        status = "offline"

        # Fetch endpoint from ClickHouse
        result = self.ch.query(
            "SELECT endpoint FROM omniwatch.regions WHERE region_id = {region_id:String}",
            parameters={"region_id": region_id},
        )

        if not result.result_rows:
            logger.warning("Region %s not found", region_id)
            return {"region_id": region_id, "status": "unknown"}

        endpoint = result.result_rows[0][0]
        health_url = f"{endpoint.rstrip('/')}/health"

        if not validate_endpoint_url(endpoint):
            logger.warning("Blocked health check to invalid/blocked endpoint: %s", endpoint)
            return {"region_id": region_id, "status": "blocked"}

        try:
            resp = requests.get(health_url, timeout=self.HEALTH_CHECK_TIMEOUT)
            if resp.status_code == 200:
                status = "healthy"
            else:
                status = "degraded"
        except Exception as e:
            logger.warning("Health check failed for %s: %s", region_id, e)
            status = "offline"

        # Update ClickHouse
        self.ch.command(
            "ALTER TABLE omniwatch.regions UPDATE status = {status:String}, "
            "last_health_check = {checked_at:DateTime64(3, 'UTC')} "
            "WHERE region_id = {region_id:String}",
            parameters={"status": status, "checked_at": now, "region_id": region_id},
        )

        # Cache in Redis (60s TTL)
        cache_key = f"ow:federation:region:{region_id}:health"
        self.cache.setex(cache_key, 60, json.dumps({
            "region_id": region_id,
            "status": status,
            "checked_at": now.isoformat(),
        }))

        logger.info("Health check %s: %s", region_id, status)
        return {"region_id": region_id, "status": status, "checked_at": now.isoformat()}

    def get_healthy_regions(self) -> list[dict[str, Any]]:
        """Return all regions with status 'healthy'."""
        result = self.ch.query(
            "SELECT region_id, endpoint, display_name, status "
            "FROM omniwatch.regions WHERE status = {status:String}",
            parameters={"status": "healthy"},
        )

        return [
            {
                "region_id": row[0],
                "endpoint": row[1],
                "display_name": row[2],
                "status": row[3],
            }
            for row in result.result_rows
        ]

    def get_all_regions(self) -> list[dict[str, Any]]:
        """Return all registered regions with their current status."""
        result = self.ch.query(
            "SELECT region_id, endpoint, display_name, status, last_health_check "
            "FROM omniwatch.regions"
        )

        return [
            {
                "region_id": row[0],
                "endpoint": row[1],
                "display_name": row[2],
                "status": row[3],
                "last_health_check": row[4].isoformat() if row[4] else None,
            }
            for row in result.result_rows
        ]
