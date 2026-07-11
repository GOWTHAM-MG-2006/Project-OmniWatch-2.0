"""
OmniWatch 2.0 — Performance Testing
Component: Memory Optimizer
Phase: 7
Purpose: Memory profiling and optimization
Inputs: System memory metrics
Outputs: Memory profile, leak detection, recommendations
Technology: Python, tracemalloc, psutil
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class MemoryOptimizer:
    """Memory optimization utilities."""

    def __init__(self):
        self._allocations: dict[str, int] = {}

    def profile_memory(self) -> dict[str, Any]:
        """Profile current memory usage."""
        if HAS_PSUTIL:
            mem = psutil.virtual_memory()
            return {
                "used_mb": round(mem.used / (1024 * 1024), 2),
                "available_mb": round(mem.available / (1024 * 1024), 2),
                "percent_used": mem.percent,
            }
        return {"used_mb": 0, "available_mb": 0, "percent_used": 0}

    def detect_leaks(self) -> list[dict]:
        """Detect potential memory leaks."""
        leaks = []
        for obj_name, size in self._allocations.items():
            if size > 1024 * 1024:
                leaks.append({"object": obj_name, "size_mb": round(size / (1024 * 1024), 2)})
        return leaks

    def get_recommendations(self) -> list[dict]:
        """Get memory optimization recommendations."""
        recommendations = []
        profile = self.profile_memory()
        if profile.get("percent_used", 0) > 80:
            recommendations.append({
                "severity": "high",
                "message": "Memory usage >80%, consider scaling or optimizing queries",
            })
        return recommendations

    def track_allocation(self, name: str, size_bytes: int) -> None:
        """Track object allocation."""
        self._allocations[name] = self._allocations.get(name, 0) + size_bytes
