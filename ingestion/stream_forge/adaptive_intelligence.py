"""
OmniWatch 2.0 — StreamForge
Component: Adaptive Intelligence
Layer: 3
Phase: 1
Purpose: Tail-based sampling and anomaly-prioritized routing
Inputs: Enriched telemetry events with anomaly scores
Outputs: Sampled events routed to appropriate consumers
"""

import os
import json
import logging
import random
from typing import Any
from collections import defaultdict

logger = logging.getLogger(__name__)

# Sampling rates by priority
SAMPLING_RATES = {
    "critical": 1.0,    # Sample 100% of critical events
    "high": 0.8,        # Sample 80% of high-priority events
    "medium": 0.3,      # Sample 30% of medium-priority events
    "low": 0.1,         # Sample 10% of low-priority events
    "normal": 0.05,     # Sample 5% of normal events
}

# Anomaly score thresholds
ANOMALY_THRESHOLDS = {
    "critical": 0.9,
    "high": 0.7,
    "medium": 0.4,
    "low": 0.2,
}


class AdaptiveIntelligence:
    """Tail-based sampling and anomaly-prioritized event routing."""

    def __init__(self, base_sampling_rate: float = 0.1):
        self.base_sampling_rate = base_sampling_rate
        self._event_counts: dict[str, int] = defaultdict(int)
        self._sampled_counts: dict[str, int] = defaultdict(int)

    def should_sample(self, event: dict[str, Any]) -> bool:
        """Determine if an event should be sampled based on anomaly score and priority."""
        anomaly_score = event.get("anomaly_score", 0)
        priority = self._get_priority(anomaly_score, event)
        sampling_rate = SAMPLING_RATES.get(priority, self.base_sampling_rate)

        # Always sample if anomaly score is above critical threshold
        if anomaly_score >= ANOMALY_THRESHOLDS["critical"]:
            return True

        # Track counts
        entity_id = event.get("entity_id", "unknown")
        self._event_counts[entity_id] += 1

        # Probabilistic sampling
        sampled = random.random() < sampling_rate
        if sampled:
            self._sampled_counts[entity_id] += 1

        return sampled

    def route_anomaly(self, event: dict[str, Any]) -> str:
        """Route an anomaly event to the appropriate consumer topic."""
        anomaly_score = event.get("anomaly_score", 0)
        entity_type = event.get("entity_type", "unknown")

        if anomaly_score >= ANOMALY_THRESHOLDS["critical"]:
            return "omniwatch.anomalies.detected"
        elif entity_type == "security":
            return "omniwatch.security.events"
        elif anomaly_score >= ANOMALY_THRESHOLDS["medium"]:
            return "omniwatch.anomalies.detected"
        else:
            return "omniwatch.metrics.raw"

    def get_sampling_stats(self) -> dict[str, Any]:
        """Get sampling statistics."""
        total_events = sum(self._event_counts.values())
        total_sampled = sum(self._sampled_counts.values())
        return {
            "total_events": total_events,
            "total_sampled": total_sampled,
            "effective_rate": total_sampled / total_events if total_events > 0 else 0,
            "per_entity": {
                entity: {
                    "total": self._event_counts[entity],
                    "sampled": self._sampled_counts[entity],
                }
                for entity in self._event_counts
            },
        }

    @staticmethod
    def _get_priority(anomaly_score: float, event: dict[str, Any]) -> str:
        """Determine event priority from anomaly score and context."""
        if anomaly_score >= ANOMALY_THRESHOLDS["critical"]:
            return "critical"
        elif anomaly_score >= ANOMALY_THRESHOLDS["high"]:
            return "high"
        elif anomaly_score >= ANOMALY_THRESHOLDS["medium"]:
            return "medium"
        elif anomaly_score >= ANOMALY_THRESHOLDS["low"]:
            return "low"
        return "normal"
