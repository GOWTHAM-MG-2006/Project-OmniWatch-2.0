"""
OmniWatch 2.0 — GhostCollector
Component: Health Monitor (Watchdog)
Layer: 2
Phase: 5
Purpose: Self-healing health monitor with exponential backoff
Inputs: GhostCollector sub-process status
Outputs: Restart commands, CPU/memory enforcement
Technology: Python
"""

import os
import logging
import time
import random
from typing import Any, Callable

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitors GhostCollector sub-processes and auto-restarts on failure."""

    def __init__(
        self,
        check_interval: float = 10.0,
        max_backoff: float = 60.0,
        cpu_budget_percent: float = 1.0,
        memory_limit_mb: int = 512,
    ):
        self.check_interval = check_interval
        self.max_backoff = max_backoff
        self.cpu_budget = cpu_budget_percent
        self.memory_limit = memory_limit_mb
        self._processes: dict[str, dict[str, Any]] = {}
        self._restart_counts: dict[str, int] = {}
        self._last_restart: dict[str, float] = {}
        self._current_backoff: dict[str, float] = {}

    def register_process(self, name: str, health_check: Callable[[], bool], restart_fn: Callable[[], bool]) -> None:
        """Register a sub-process for monitoring.

        Args:
            name: Process identifier.
            health_check: Function that returns True if healthy.
            restart_fn: Function to restart the process.
        """
        self._processes[name] = {
            "health_check": health_check,
            "restart_fn": restart_fn,
            "status": "unknown",
            "last_check": 0,
        }
        self._restart_counts[name] = 0
        self._current_backoff[name] = 1.0
        logger.info("Registered process for monitoring: %s", name)

    def check_all(self) -> dict[str, Any]:
        """Check health of all registered processes.

        Returns:
            Dict with per-process status and actions taken.
        """
        results = {}
        for name, proc in self._processes.items():
            try:
                healthy = proc["health_check"]()
                proc["last_check"] = time.time()

                if healthy:
                    proc["status"] = "healthy"
                    self._current_backoff[name] = 1.0
                    results[name] = {"status": "healthy", "action": "none"}
                else:
                    proc["status"] = "unhealthy"
                    action = self._attempt_restart(name, proc)
                    results[name] = {"status": "unhealthy", "action": action}
            except Exception as e:
                proc["status"] = "error"
                results[name] = {"status": "error", "action": "check_failed", "error": str(e)}

        return results

    def _attempt_restart(self, name: str, proc: dict) -> str:
        """Attempt to restart a failed process with exponential backoff."""
        now = time.time()
        backoff = self._current_backoff[name]
        last = self._last_restart.get(name, 0)

        if now - last < backoff:
            return f"backoff ({backoff:.0f}s remaining)"

        try:
            success = proc["restart_fn"]()
            if success:
                self._restart_counts[name] += 1
                self._last_restart[name] = now
                self._current_backoff[name] = min(backoff * 2, self.max_backoff)
                logger.warning("Restarted process %s (restart #%d)", name, self._restart_counts[name])
                return "restarted"
            return "restart_failed"
        except Exception as e:
            logger.error("Restart failed for %s: %s", name, e)
            return "restart_error"

    def enforce_cpu_budget(self, current_cpu_percent: float) -> bool:
        """Reduce fidelity if CPU budget exceeded.

        Returns:
            True if CPU is within budget, False if throttling needed.
        """
        if current_cpu_percent > self.cpu_budget:
            logger.warning("CPU budget exceeded: %.1f%% > %.1f%%", current_cpu_percent, self.cpu_budget)
            return False
        return True

    def get_stats(self) -> dict[str, Any]:
        """Get watchdog statistics."""
        return {
            "processes": len(self._processes),
            "healthy": sum(1 for p in self._processes.values() if p["status"] == "healthy"),
            "unhealthy": sum(1 for p in self._processes.values() if p["status"] != "healthy"),
            "restart_counts": dict(self._restart_counts),
            "cpu_budget_percent": self.cpu_budget,
            "memory_limit_mb": self.memory_limit,
        }
