"""Real HTTP load testing for OmniWatch API endpoints."""

import time
import statistics
import os
import logging

from config import config

logger = logging.getLogger(__name__)


class LoadTestRunner:
    """HTTP load testing with real requests and latency measurement."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.DASHBOARD_BACKEND_URL
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(timeout=config.LOAD_TEST_TIMEOUT)
            except ImportError:
                logger.warning("httpx not installed — load testing unavailable")
                return None
        return self._client

    def _make_request(self, method: str, path: str) -> float:
        """Make a real HTTP request and return latency in ms."""
        start = time.perf_counter()
        try:
            if self.client:
                self.client.request(method, f"{self.base_url}{path}")
        except Exception as e:
            logger.warning("Request failed: %s", e)
        return (time.perf_counter() - start) * 1000

    def test_api_latency(self, endpoint: str, method: str = "GET",
                         iterations: int = 50) -> dict:
        """Measure real API latency for an endpoint."""
        if not self.client:
            return {"endpoint": endpoint, "error": "httpx not installed"}

        latencies = []
        for _ in range(iterations):
            latencies.append(self._make_request(method, endpoint))

        latencies.sort()
        return {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "p50_ms": round(statistics.median(latencies), 1),
            "p95_ms": round(latencies[int(len(latencies) * 0.95)], 1),
            "p99_ms": round(latencies[int(len(latencies) * 0.99)], 1),
            "avg_ms": round(statistics.mean(latencies), 1),
            "min_ms": round(min(latencies), 1),
            "max_ms": round(max(latencies), 1),
        }

    def run_full_suite(self) -> dict:
        """Run load tests against all major endpoints."""
        endpoints = [
            "/health",
            "/api/v1/incidents",
            "/api/v1/metrics/summary",
            "/api/v1/status",
            "/api/v1/knowledge",
        ]
        results = {}
        for ep in endpoints:
            results[ep] = self.test_api_latency(ep)
        if self._client:
            self._client.close()
        return results
