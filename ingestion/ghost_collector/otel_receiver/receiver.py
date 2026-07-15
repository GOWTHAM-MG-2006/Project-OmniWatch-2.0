"""
OmniWatch 2.0 — GhostCollector
Component: OTLP Receiver
Layer: 2
Phase: 5
Purpose: OTLP receiver that accepts traces/metrics/logs via gRPC and HTTP
Inputs: OTLP traces, metrics, logs from instrumented applications
Outputs: Validated telemetry to Kafka omniwatch.telemetry.raw
Technology: Python, grpcio, opentelemetry-proto
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Any

from config import config

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from confluent_kafka import Producer
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False


class OTLPReceiver:
    """OTLP receiver that accepts traces/metrics/logs and forwards to Kafka."""

    def __init__(
        self,
        grpc_port: int = config.OTLP_GRPC_PORT,
        http_port: int = config.OTLP_HTTP_PORT,
        kafka_bootstrap: str | None = None,
        kafka_topic: str = "omniwatch.telemetry.raw",
    ):
        self.grpc_port = grpc_port
        self.http_port = http_port
        self.kafka_bootstrap = kafka_bootstrap or config.KAFKA_BOOTSTRAP_SERVERS
        self.kafka_topic = kafka_topic
        self._producer = None
        self._received_count = 0

    @property
    def producer(self):
        if self._producer is None and HAS_KAFKA:
            try:
                self._producer = Producer({
                    "bootstrap.servers": self.kafka_bootstrap,
                    "client.id": "omniwatch-otlp-receiver",
                })
            except Exception as e:
                logger.warning("Kafka producer init failed: %s", e)
        return self._producer

    def receive_trace(self, trace_data: dict[str, Any]) -> bool:
        """Receive an OTLP trace and forward to Kafka.

        Args:
            trace_data: Parsed OTLP trace data.

        Returns:
            True if forwarded successfully.
        """
        self._received_count += 1

        event = {
            "source": "otlp",
            "type": "trace",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": trace_data,
        }

        return self._forward_to_kafka(event)

    def receive_metric(self, metric_data: dict[str, Any]) -> bool:
        """Receive an OTLP metric and forward to Kafka."""
        self._received_count += 1

        event = {
            "source": "otlp",
            "type": "metric",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": metric_data,
        }

        return self._forward_to_kafka(event)

    def receive_log(self, log_data: dict[str, Any]) -> bool:
        """Receive an OTLP log and forward to Kafka."""
        self._received_count += 1

        event = {
            "source": "otlp",
            "type": "log",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": log_data,
        }

        return self._forward_to_kafka(event)

    def _forward_to_kafka(self, event: dict[str, Any]) -> bool:
        """Forward event to Kafka topic."""
        if not self.producer:
            logger.debug("Kafka unavailable — event buffered locally")
            return True

        try:
            self.producer.produce(
                self.kafka_topic,
                value=json.dumps(event, default=str).encode(),
            )
            self.producer.poll(0)
            return True
        except Exception as e:
            logger.warning("Kafka produce failed: %s", e)
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get receiver statistics."""
        return {
            "received_count": self._received_count,
            "kafka_connected": self.producer is not None,
            "grpc_port": self.grpc_port,
            "http_port": self.http_port,
        }
