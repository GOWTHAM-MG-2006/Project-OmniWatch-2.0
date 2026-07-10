"""
OmniWatch 2.0 — Performance Testing
Component: Load Test
Phase: 5
Purpose: Locust-based load testing for OmniWatch components
Inputs: Target endpoints and load parameters
Outputs: Performance report with throughput, latency, error rate
Technology: Python, locust (optional), requests
"""

import json
import time
import logging
import statistics
from datetime import datetime, timezone
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logger = logging.getLogger(__name__)


class LoadTester:
    """Load testing framework for OmniWatch components."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: list[dict[str, Any]] = []

    def test_health_endpoint(self, concurrency: int = 10, duration_seconds: int = 30) -> dict:
        """Test /health endpoint under load."""
        return self._run_load_test(
            endpoint="/health",
            concurrency=concurrency,
            duration_seconds=duration_seconds,
            name="health_check",
        )

    def test_api_endpoints(self, concurrency: int = 5, duration_seconds: int = 30) -> list[dict]:
        """Test all API endpoints under load."""
        endpoints = [
            "/api/incidents",
            "/api/topology",
            "/api/metrics",
            "/api/approvals",
            "/api/knowledge",
            "/api/simulations",
            "/api/security",
            "/api/config-drift",
            "/api/reports",
        ]

        results = []
        for endpoint in endpoints:
            result = self._run_load_test(
                endpoint=endpoint,
                concurrency=concurrency,
                duration_seconds=duration_seconds,
                name=endpoint.replace("/", "_").strip("_"),
            )
            results.append(result)

        return results

    def _run_load_test(
        self,
        endpoint: str,
        concurrency: int,
        duration_seconds: int,
        name: str,
    ) -> dict:
        """Run a load test against a single endpoint."""
        latencies = []
        errors = 0
        total_requests = 0
        start_time = time.time()

        def make_request():
            nonlocal errors, total_requests
            try:
                if HAS_REQUESTS:
                    resp = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                    return resp.status_code, resp.elapsed.total_seconds()
                else:
                    # Mock response
                    time.sleep(0.01)
                    return 200, 0.01
            except Exception:
                errors += 1
                return 0, 0

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            while time.time() - start_time < duration_seconds:
                futures = [executor.submit(make_request) for _ in range(concurrency)]
                for future in as_completed(futures):
                    status, latency = future.result()
                    total_requests += 1
                    if status == 200:
                        latencies.append(latency)
                    time.sleep(0.001)

        elapsed = time.time() - start_time
        throughput = total_requests / elapsed if elapsed > 0 else 0

        result = {
            "test_name": name,
            "endpoint": endpoint,
            "concurrency": concurrency,
            "duration_seconds": round(elapsed, 1),
            "total_requests": total_requests,
            "successful_requests": len(latencies),
            "failed_requests": errors,
            "throughput_rps": round(throughput, 1),
            "error_rate": round(errors / max(total_requests, 1) * 100, 2),
            "latency_p50": round(statistics.median(latencies) * 1000, 2) if latencies else 0,
            "latency_p95": round(sorted(latencies)[int(len(latencies) * 0.95)] * 1000, 2) if latencies else 0,
            "latency_p99": round(sorted(latencies)[int(len(latencies) * 0.99)] * 1000, 2) if latencies else 0,
            "latency_avg": round(statistics.mean(latencies) * 1000, 2) if latencies else 0,
        }

        self.results.append(result)
        return result

    def generate_report(self) -> str:
        """Generate a markdown performance report."""
        lines = [
            "# OmniWatch 2.0 — Load Test Report",
            f"\n**Generated:** {datetime.now(timezone.utc).isoformat()}",
            f"\n## Results\n",
            "| Test | Throughput | P50 | P95 | P99 | Error Rate |",
            "|------|-----------|-----|-----|-----|------------|",
        ]

        for r in self.results:
            lines.append(
                f"| {r['test_name']} | {r['throughput_rps']} req/s | "
                f"{r['latency_p50']}ms | {r['latency_p95']}ms | {r['latency_p99']}ms | "
                f"{r['error_rate']}% |"
            )

        return "\n".join(lines)
