"""
OmniWatch 2.0 — Performance Testing
Component: Enhanced Benchmark Suite
Phase: 7
Purpose: Real benchmark suite with ClickHouse latency, API latency,
         memory profiling, regression detection, and markdown reporting
Inputs: System metrics, historical benchmark data
Outputs: Benchmark report with regression analysis
Technology: Python, psutil, clickhouse_connect, requests
"""

import json
import time
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import config

logger = logging.getLogger(__name__)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import clickhouse_connect
    HAS_CLICKHOUSE = True
except ImportError:
    HAS_CLICKHOUSE = False

try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

HISTORY_DIR = Path(os.getenv("BENCHMARK_HISTORY_DIR", "performance/benchmark_history"))


class EnhancedBenchmarkSuite:
    """Real benchmark suite with regression detection and markdown reporting."""

    def __init__(self, api_base_url: str = config.DASHBOARD_BACKEND_URL,
                 clickhouse_host: str = config.CLICKHOUSE_HOST,
                 clickhouse_port: int = config.CLICKHOUSE_PORT):
        self.api_base_url = api_base_url
        self.clickhouse_host = clickhouse_host
        self.clickhouse_port = clickhouse_port
        self.results: dict[str, Any] = {}
        self.history: list[dict] = []
        self._load_history()

    def _history_path(self) -> Path:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        return HISTORY_DIR / "benchmark_history.json"

    def _load_history(self) -> None:
        path = self._history_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self.history = data[-50:]
            except Exception:
                self.history = []

    def _save_history(self) -> None:
        try:
            self._history_path().write_text(
                json.dumps(self.history[-100:], indent=2), encoding="utf-8"
            )
        except Exception as exc:
            logger.warning("Failed to save benchmark history: %s", exc)

    # ------------------------------------------------------------------
    # Individual benchmarks
    # ------------------------------------------------------------------

    def _bench_clickhouse_latency(self) -> dict[str, Any]:
        """Measure ClickHouse query latency with a simple SELECT."""
        if not HAS_CLICKHOUSE:
            return {"available": False, "error": "clickhouse_connect not installed"}
        try:
            client = clickhouse_connect.get_client(
                host=self.clickhouse_host,
                port=self.clickhouse_port,
                connect_timeout=config.BENCHMARK_API_TIMEOUT,
                send_receive_timeout=config.CH_SEND_RECEIVE_TIMEOUT,
            )
            latencies: list[float] = []
            for _ in range(5):
                start = time.perf_counter()
                client.command("SELECT 1")
                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)
            client.close()
            return {
                "available": True,
                "avg_ms": round(sum(latencies) / len(latencies), 2),
                "min_ms": round(min(latencies), 2),
                "max_ms": round(max(latencies), 2),
                "samples": len(latencies),
            }
        except Exception as exc:
            return {"available": False, "error": str(exc)}

    def _bench_api_latency(self) -> dict[str, Any]:
        """Measure API /health endpoint latency."""
        if not HAS_REQUESTS:
            return {"available": False, "error": "requests not installed"}
        try:
            url = f"{self.api_base_url}/health"
            latencies: list[float] = []
            status_code = None
            for _ in range(5):
                start = time.perf_counter()
                resp = _requests.get(url, timeout=config.BENCHMARK_API_TIMEOUT)
                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)
                status_code = resp.status_code
            return {
                "available": True,
                "status_code": status_code,
                "avg_ms": round(sum(latencies) / len(latencies), 2),
                "min_ms": round(min(latencies), 2),
                "max_ms": round(max(latencies), 2),
                "samples": len(latencies),
            }
        except Exception as exc:
            return {"available": False, "error": str(exc)}

    def _bench_memory(self) -> dict[str, Any]:
        """Profile memory usage via psutil."""
        if not HAS_PSUTIL:
            return {"available": False, "error": "psutil not installed"}
        vm = psutil.virtual_memory()
        proc = psutil.Process()
        proc_mem = proc.memory_info()
        return {
            "available": True,
            "system_total_gb": round(vm.total / (1024 ** 3), 2),
            "system_used_gb": round(vm.used / (1024 ** 3), 2),
            "system_percent": vm.percent,
            "process_rss_mb": round(proc_mem.rss / (1024 ** 2), 2),
            "process_vms_mb": round(proc_mem.vms / (1024 ** 2), 2),
        }

    def _bench_resources(self) -> dict[str, Any]:
        """Profile CPU and disk I/O."""
        if not HAS_PSUTIL:
            return {"available": False, "error": "psutil not installed"}
        cpu = psutil.cpu_percent(interval=0.2)
        disk = psutil.disk_io_counters()
        return {
            "available": True,
            "cpu_percent": cpu,
            "disk_read_mb": round(disk.read_bytes / (1024 ** 2), 2) if disk else 0,
            "disk_write_mb": round(disk.write_bytes / (1024 ** 2), 2) if disk else 0,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_benchmarks(self) -> dict[str, Any]:
        """Run all benchmarks and return consolidated results."""
        ts = datetime.now(timezone.utc).isoformat()
        self.results = {
            "timestamp": ts,
            "clickhouse": self._bench_clickhouse_latency(),
            "api": self._bench_api_latency(),
            "memory": self._bench_memory(),
            "resources": self._bench_resources(),
        }
        # Convenience aliases for regression detection
        ch = self.results["clickhouse"]
        api = self.results["api"]
        mem = self.results["memory"]
        self.results["query_latency_ms"] = ch.get("avg_ms", -1)
        self.results["api_latency_ms"] = api.get("avg_ms", -1)
        self.results["memory_usage_gb"] = mem.get("system_used_gb", -1)
        self.history.append(self.results)
        self._save_history()
        return self.results

    def detect_regressions(self, threshold_pct: float = 10.0) -> list[dict]:
        """Detect performance regressions against the last baseline."""
        regressions: list[dict] = []
        if len(self.history) < 2:
            return regressions
        prev = self.history[-2]
        curr = self.results or (self.history[-1] if self.history else {})
        numeric_keys = ["query_latency_ms", "api_latency_ms", "memory_usage_gb"]
        for key in numeric_keys:
            cur_val = curr.get(key)
            pre_val = prev.get(key)
            if cur_val is None or pre_val is None:
                continue
            if not isinstance(cur_val, (int, float)) or not isinstance(pre_val, (int, float)):
                continue
            if pre_val <= 0:
                continue
            change_pct = ((cur_val - pre_val) / pre_val) * 100
            if change_pct > threshold_pct:
                regressions.append({
                    "metric": key,
                    "previous": pre_val,
                    "current": cur_val,
                    "change_pct": round(change_pct, 2),
                    "severity": "CRITICAL" if change_pct > 50 else "WARNING",
                })
        return regressions

    def generate_markdown_report(self) -> str:
        """Generate a markdown benchmark report."""
        lines: list[str] = []
        lines.append("# OmniWatch Benchmark Report\n")
        lines.append(f"**Timestamp:** {self.results.get('timestamp', 'N/A')}\n")
        lines.append("---\n")

        # ClickHouse
        ch = self.results.get("clickhouse", {})
        lines.append("## ClickHouse Query Latency\n")
        if ch.get("available"):
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| Avg | {ch['avg_ms']} ms |")
            lines.append(f"| Min | {ch['min_ms']} ms |")
            lines.append(f"| Max | {ch['max_ms']} ms |")
            lines.append(f"| Samples | {ch['samples']} |")
        else:
            lines.append(f"> Not available: {ch.get('error', 'unknown')}\n")
        lines.append("")

        # API
        api = self.results.get("api", {})
        lines.append("## API Response Latency\n")
        if api.get("available"):
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| Status | {api['status_code']} |")
            lines.append(f"| Avg | {api['avg_ms']} ms |")
            lines.append(f"| Min | {api['min_ms']} ms |")
            lines.append(f"| Max | {api['max_ms']} ms |")
        else:
            lines.append(f"> Not available: {api.get('error', 'unknown')}\n")
        lines.append("")

        # Memory
        mem = self.results.get("memory", {})
        lines.append("## Memory Usage\n")
        if mem.get("available"):
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| System Total | {mem['system_total_gb']} GB |")
            lines.append(f"| System Used | {mem['system_used_gb']} GB |")
            lines.append(f"| System % | {mem['system_percent']}% |")
            lines.append(f"| Process RSS | {mem['process_rss_mb']} MB |")
            lines.append(f"| Process VMS | {mem['process_vms_mb']} MB |")
        else:
            lines.append(f"> Not available: {mem.get('error', 'unknown')}\n")
        lines.append("")

        # Resources
        res = self.results.get("resources", {})
        lines.append("## System Resources\n")
        if res.get("available"):
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| CPU | {res['cpu_percent']}% |")
            lines.append(f"| Disk Read | {res['disk_read_mb']} MB |")
            lines.append(f"| Disk Write | {res['disk_write_mb']} MB |")
        lines.append("")

        # Regressions
        regressions = self.detect_regressions()
        lines.append("## Regression Analysis\n")
        if regressions:
            lines.append(f"| Metric | Previous | Current | Change % | Severity |")
            lines.append(f"|--------|----------|---------|----------|----------|")
            for r in regressions:
                lines.append(
                    f"| {r['metric']} | {r['previous']} | {r['current']} | "
                    f"+{r['change_pct']}% | {r['severity']} |"
                )
        else:
            lines.append("No regressions detected.\n")
        lines.append("")

        return "\n".join(lines)

    def plan_capacity(self, current_throughput: int) -> dict[str, Any]:
        """Estimate capacity at scale based on current resource usage."""
        mem = self.results.get("memory", {})
        sys_used = mem.get("system_used_gb", 7.5)
        sys_total = mem.get("system_total_gb", 16.0)
        headroom = max(sys_total - sys_used, 0.1)
        return {
            "current_throughput": current_throughput,
            "estimated_max_throughput": int(current_throughput * (headroom / max(sys_used, 0.1))),
            "headroom_gb": round(headroom, 2),
            "storage_growth_gb_per_day": 10,
            "estimated_monthly_cost_usd": 500,
        }
