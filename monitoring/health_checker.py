"""
OmniWatch 2.0 — Monitoring
Component: Health Checker
Phase: 5
Purpose: Continuous health monitoring of all OmniWatch components
Inputs: Service endpoints, Docker containers, system metrics
Outputs: Health status with alerts
Technology: Python, requests, redis, docker
"""

import os
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class HealthChecker:
    """Continuous health monitoring of all OmniWatch components."""

    def __init__(self):
        self.checks: dict[str, dict] = {}

    def check_docker_containers(self) -> dict[str, Any]:
        """Check if all Docker containers are running."""
        containers = [
            "omniwatch-kafka", "omniwatch-clickhouse", "omniwatch-minio",
            "omniwatch-redis", "omniwatch-opa", "omniwatch-ollama",
            "omniwatch-dashboard-backend", "omniwatch-dashboard-frontend",
        ]

        results = {}
        for name in containers:
            try:
                import subprocess
                proc = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Status}}", name],
                    capture_output=True, text=True, timeout=5,
                )
                status = proc.stdout.strip()
                results[name] = {
                    "status": "up" if status == "running" else "down",
                    "level": "ok" if status == "running" else "critical",
                }
            except Exception:
                results[name] = {"status": "unknown", "level": "warning"}

        return results

    def check_api_endpoints(self) -> dict[str, Any]:
        """Check if API endpoints are responding."""
        endpoints = {
            "dashboard_backend": "http://localhost:8000/health",
            "minio": "http://localhost:9002/minio/health/live",
            "opa": "http://localhost:8181/health",
            "ollama": "http://localhost:11434/api/tags",
        }

        results = {}
        for name, url in endpoints.items():
            if HAS_REQUESTS:
                try:
                    resp = requests.get(url, timeout=3)
                    results[name] = {
                        "status": "up" if resp.status_code < 400 else "degraded",
                        "level": "ok" if resp.status_code < 400 else "warning",
                        "status_code": resp.status_code,
                    }
                except Exception:
                    results[name] = {"status": "down", "level": "critical"}
            else:
                results[name] = {"status": "unknown", "level": "warning"}

        return results

    def check_redis_memory(self) -> dict[str, Any]:
        """Check Redis memory usage."""
        try:
            import redis
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            info = r.info("memory")
            used_mb = info.get("used_memory", 0) / 1024 / 1024
            return {
                "used_mb": round(used_mb, 1),
                "level": "ok" if used_mb < 400 else "warning",
            }
        except Exception:
            return {"used_mb": 0, "level": "unknown"}

    def run_all_checks(self) -> dict[str, Any]:
        """Run all health checks."""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "docker": self.check_docker_containers(),
            "api": self.check_api_endpoints(),
            "redis": self.check_redis_memory(),
        }

        # Count alerts
        critical = 0
        warnings = 0
        for section in ["docker", "api"]:
            for name, check in results[section].items():
                if check.get("level") == "critical":
                    critical += 1
                elif check.get("level") == "warning":
                    warnings += 1

        results["summary"] = {
            "critical": critical,
            "warnings": warnings,
            "healthy": critical == 0 and warnings == 0,
        }

        return results
