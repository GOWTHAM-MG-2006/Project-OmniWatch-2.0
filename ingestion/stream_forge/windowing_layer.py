"""
OmniWatch 2.0 — StreamForge
Component: Windowing Layer
Layer: 3
Phase: 1
Purpose: Flink-compatible tumbling windows with feature engineering for ML-ready vectors
Inputs: Entity-resolved telemetry streams
Outputs: Windowed feature vectors for anomaly detection
"""

import os
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class WindowingLayer:
    """Tumbling window aggregation with feature engineering."""

    def __init__(self, window_size_seconds: int = 60, slide_interval_seconds: int = 10):
        self.window_size = window_size_seconds
        self.slide_interval = slide_interval_seconds
        self._windows: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._window_starts: dict[str, float] = {}

    def add_event(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Add an event and return any completed window feature vectors."""
        entity_id = event.get("entity_id", "unknown")
        timestamp = event.get("timestamp", time.time())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()

        # Determine window key
        window_key = f"{entity_id}:{event.get('metric_name', 'default')}"
        window_start = self._get_window_start(timestamp)

        # Initialize window tracking
        if window_key not in self._window_starts:
            self._window_starts[window_key] = window_start

        # Check if window has rolled over
        completed_vectors = []
        if window_start > self._window_starts[window_key]:
            # Window completed — compute features
            if self._windows[window_key]:
                feature_vector = self._compute_features(
                    window_key, self._windows[window_key]
                )
                completed_vectors.append(feature_vector)
            # Start new window
            self._windows[window_key] = []
            self._window_starts[window_key] = window_start

        self._windows[window_key].append(event)
        return completed_vectors

    def flush_all_windows(self) -> list[dict[str, Any]]:
        """Force-flush all open windows (e.g., on shutdown)."""
        vectors = []
        for window_key, events in self._windows.items():
            if events:
                vectors.append(self._compute_features(window_key, events))
        self._windows.clear()
        self._window_starts.clear()
        return vectors

    def _get_window_start(self, timestamp: float) -> float:
        """Get the start time of the window containing this timestamp."""
        return (timestamp // self.window_size) * self.window_size

    def _compute_features(
        self, window_key: str, events: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Compute ML-ready feature vectors from windowed events."""
        entity_id, metric_name = window_key.split(":", 1)

        values = [e.get("metric_value", 0) for e in events if "metric_value" in e]
        timestamps = [e.get("timestamp", 0) for e in events]

        if not values:
            values = [0]

        # Basic statistical features
        sorted_vals = sorted(values)
        n = len(sorted_vals)

        features = {
            "entity_id": entity_id,
            "metric_name": metric_name,
            "window_start": min(timestamps) if timestamps else time.time(),
            "window_end": max(timestamps) if timestamps else time.time(),
            "window_size_seconds": self.window_size,
            "event_count": n,
            "mean": sum(values) / n,
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
            "std_dev": self._std_dev(values),
            "p50": sorted_vals[n // 2],
            "p95": sorted_vals[int(n * 0.95)] if n > 1 else sorted_vals[0],
            "p99": sorted_vals[int(n * 0.99)] if n > 1 else sorted_vals[0],
        }

        # Rate of change
        if len(values) >= 2:
            features["rate_of_change"] = (values[-1] - values[0]) / len(values)
        else:
            features["rate_of_change"] = 0

        # Add topology context from last event
        if events:
            last_event = events[-1]
            features["entity_type"] = last_event.get("entity_type", "unknown")
            features["topology_context"] = last_event.get("topology_context", {})

        return features

    @staticmethod
    def _std_dev(values: list[float]) -> float:
        """Compute standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

    def get_window_state(self) -> dict[str, Any]:
        """Get current window state for monitoring."""
        return {
            "active_windows": len(self._windows),
            "total_events": sum(len(e) for e in self._windows.values()),
            "window_size_seconds": self.window_size,
        }
