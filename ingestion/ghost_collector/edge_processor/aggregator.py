"""
OmniWatch 2.0 — GhostCollector
Component: Edge Processor
Layer: 2
Phase: 5
Purpose: In-agent edge computing — aggregates metrics, only exports anomalies
Inputs: Raw telemetry events
Outputs: Aggregated/anomalous events only (reduces bandwidth by >80%)
Technology: Python
"""

import logging
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class EdgeAggregator:
    """Aggregates metrics locally and only exports anomalies."""

    def __init__(
        self,
        aggregation_window_seconds: float = 10.0,
        anomaly_threshold: float = 0.7,
    ):
        self.window = aggregation_window_seconds
        self.threshold = anomaly_threshold
        self._buffers: dict[str, list[dict]] = defaultdict(list)
        self._window_start: dict[str, float] = {}
        self._total_received = 0
        self._total_exported = 0

    def process_event(self, event: dict[str, Any]) -> dict[str, Any] | None:
        """Process an event through edge aggregation.

        Args:
            event: Raw telemetry event.

        Returns:
            Aggregated event if should be exported, None otherwise.
        """
        self._total_received += 1
        entity_id = event.get("entity_id", "unknown")
        now = time.time()

        # Check window boundary
        if entity_id not in self._window_start or (now - self._window_start[entity_id]) >= self.window:
            # Flush previous window
            result = self._flush_window(entity_id)
            self._buffers[entity_id] = []
            self._window_start[entity_id] = now

            if result:
                self._total_exported += 1
                return result

        # Buffer event
        self._buffers[entity_id].append(event)
        return None

    def _flush_window(self, entity_id: str) -> dict[str, Any] | None:
        """Flush the aggregation window and check for anomalies."""
        events = self._buffers.get(entity_id, [])
        if not events:
            return None

        # Compute window statistics
        values = [e.get("anomaly_score", e.get("value", 0)) for e in events if isinstance(e.get("anomaly_score", e.get("value", 0)), (int, float))]
        if not values:
            return None

        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        max_val = max(values)
        min_val = min(values)

        # Check if any value exceeds anomaly threshold
        has_anomaly = max_val >= self.threshold or (std > 0 and (max_val - mean) / max(std, 0.01) > 3)

        if has_anomaly:
            return {
                "entity_id": entity_id,
                "event_type": "aggregated",
                "window_seconds": self.window,
                "sample_count": len(events),
                "mean": round(mean, 4),
                "std": round(std, 4),
                "min": round(min_val, 4),
                "max": round(max_val, 4),
                "has_anomaly": True,
                "timestamp": events[-1].get("timestamp", ""),
            }

        return None

    def get_stats(self) -> dict[str, Any]:
        """Get aggregation statistics."""
        reduction = 0
        if self._total_received > 0:
            reduction = round((1 - self._total_exported / self._total_received) * 100, 1)

        return {
            "total_received": self._total_received,
            "total_exported": self._total_exported,
            "reduction_percent": reduction,
            "window_seconds": self.window,
            "threshold": self.threshold,
        }
