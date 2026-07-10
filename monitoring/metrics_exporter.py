"""
OmniWatch 2.0 — Monitoring
Component: Metrics Exporter
Phase: 5
Purpose: Exports OmniWatch operational metrics to Prometheus format
Inputs: System metrics from all components
Outputs: Prometheus-compatible metrics text
Technology: Python, prometheus_client (optional)
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

# Define Prometheus metrics (if available)
if HAS_PROMETHEUS:
    INGESTION_RATE = Counter("omniwatch_ingestion_rate", "Events ingested per second")
    QUERY_LATENCY = Histogram("omniwatch_query_latency_seconds", "Query latency", buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0])
    ACTIVE_INCIDENTS = Gauge("omniwatch_active_incidents", "Number of active incidents")
    REMEDIATION_SUCCESS = Gauge("omniwatch_remediation_success_rate", "Remediation success rate")
    COMPONENT_HEALTH = Gauge("omniwatch_component_health", "Component health (0=down, 1=up)", ["component"])
    KAFKA_LAG = Gauge("omniwatch_kafka_topic_lag", "Kafka topic lag", ["topic"])
    SIMULATION_COUNT = Counter("omniwatch_simulax_simulation_count", "Total simulations run")
    LEARNING_FEEDBACK = Counter("omniwatch_learning_feedback_count", "Total learning feedback records")


class MetricsExporter:
    """Exports OmniWatch operational metrics."""

    def __init__(self):
        self._metrics: dict[str, Any] = {}

    def record_ingestion(self, count: int) -> None:
        """Record ingestion event count."""
        if HAS_PROMETHEUS:
            INGESTION_RATE.inc(count)
        self._metrics["ingestion_rate"] = self._metrics.get("ingestion_rate", 0) + count

    def record_query_latency(self, latency_seconds: float) -> None:
        """Record query latency."""
        if HAS_PROMETHEUS:
            QUERY_LATENCY.observe(latency_seconds)

    def set_component_health(self, component: str, healthy: bool) -> None:
        """Set component health status."""
        if HAS_PROMETHEUS:
            COMPONENT_HEALTH.labels(component=component).set(1 if healthy else 0)

    def set_active_incidents(self, count: int) -> None:
        """Set active incident count."""
        if HAS_PROMETHEUS:
            ACTIVE_INCIDENTS.set(count)

    def set_remediation_success_rate(self, rate: float) -> None:
        """Set remediation success rate."""
        if HAS_PROMETHEUS:
            REMEDIATION_SUCCESS.set(rate)

    def get_metrics_text(self) -> str:
        """Get metrics in Prometheus text format."""
        if HAS_PROMETHEUS:
            return generate_latest().decode()

        # Fallback: JSON format
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": self._metrics,
        }, indent=2)

    def get_metrics_json(self) -> dict[str, Any]:
        """Get metrics as JSON dict."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": self._metrics,
        }
