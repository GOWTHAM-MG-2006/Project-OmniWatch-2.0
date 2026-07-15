"""
OmniWatch 2.0 — StreamForge
Component: Kafka Bus
Layer: 3
Phase: 1
Purpose: Kafka producer/consumer classes for all OmniWatch topics
Inputs: Raw telemetry from GhostCollector, internal events
Outputs: Published events to downstream consumers
"""

import os
import json
import logging
from typing import Any, Callable

from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic

from config import config

logger = logging.getLogger(__name__)

# All Kafka topics from AGENTS.md
KAFKA_TOPICS = {
    "telemetry_raw": "omniwatch.telemetry.raw",
    "metrics_raw": "omniwatch.metrics.raw",
    "logs_raw": "omniwatch.logs.raw",
    "traces_raw": "omniwatch.traces.raw",
    "topology_deltas": "omniwatch.topology.deltas",
    "anomalies_detected": "omniwatch.anomalies.detected",
    "incidents_created": "omniwatch.incidents.created",
    "remediation_actions": "omniwatch.remediation.actions",
    "security_events": "omniwatch.security.events",
    "config_drift": "omniwatch.config.drift",
    "simulation_results": "omniwatch.simulation.results",
}


class KafkaProducerWrapper:
    """Kafka producer for publishing events to OmniWatch topics."""

    def __init__(self, bootstrap_servers: str | None = None):
        self.bootstrap_servers = bootstrap_servers or config.KAFKA_BOOTSTRAP_SERVERS
        self._producer = None

    @property
    def producer(self) -> Producer:
        if self._producer is None:
            self._producer = Producer({
                "bootstrap.servers": self.bootstrap_servers,
                "client.id": "omniwatch-streamforge",
                "acks": "all",
                "retries": config.KAFKA_RETRIES,
                "linger.ms": config.KAFKA_LINGER_MS,
                "batch.size": config.KAFKA_BATCH_SIZE,
            })
        return self._producer

    def produce(
        self,
        topic: str,
        key: str | None,
        value: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> bool:
        """Produce a message to a Kafka topic."""
        try:
            serialized_value = json.dumps(value, default=str).encode("utf-8")
            serialized_key = key.encode("utf-8") if key else None

            kafka_headers = None
            if headers:
                kafka_headers = [(k, v.encode("utf-8")) for k, v in headers.items()]

            self.producer.produce(
                topic=topic,
                key=serialized_key,
                value=serialized_value,
                headers=kafka_headers,
                callback=self._delivery_callback,
            )
            self.producer.poll(0)
            return True
        except KafkaException as e:
            logger.error("Failed to produce to %s: %s", topic, e)
            return False

    def produce_by_name(
        self,
        topic_name: str,
        key: str | None,
        value: dict[str, Any],
    ) -> bool:
        """Produce using a topic name alias (e.g., 'telemetry_raw')."""
        topic = KAFKA_TOPICS.get(topic_name, topic_name)
        return self.produce(topic, key, value)

    def flush(self, timeout: float = 30.0):
        """Flush all pending messages."""
        self.producer.flush(timeout)

    def close(self):
        """Flush and destroy the producer."""
        if self._producer:
            self.flush()
            self._producer = None

    @staticmethod
    def _delivery_callback(err, msg):
        if err:
            logger.error("Delivery failed: %s", err)
        else:
            logger.debug("Delivered to %s [%d]", msg.topic(), msg.partition())


class KafkaConsumerWrapper:
    """Kafka consumer for consuming events from OmniWatch topics."""

    def __init__(
        self,
        topics: list[str],
        group_id: str,
        bootstrap_servers: str | None = None,
        auto_offset_reset: str = "earliest",
    ):
        self.topics = topics
        self.bootstrap_servers = bootstrap_servers or config.KAFKA_BOOTSTRAP_SERVERS
        self._consumer = None
        self._group_id = group_id
        self._auto_offset_reset = auto_offset_reset

    @property
    def consumer(self) -> Consumer:
        if self._consumer is None:
            self._consumer = Consumer({
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": self._group_id,
                "auto.offset.reset": self._auto_offset_reset,
                "enable.auto.commit": True,
                "auto.commit.interval.ms": config.KAFKA_AUTO_COMMIT_INTERVAL,
                "session.timeout.ms": config.KAFKA_SESSION_TIMEOUT,
            })
        return self._consumer

    def subscribe(self):
        """Subscribe to configured topics."""
        self.consumer.subscribe(self.topics)
        logger.info("Subscribed to topics: %s", self.topics)

    def consume(
        self,
        callback: Callable[[str, dict[str, Any]], None],
        timeout: float = 1.0,
        max_messages: int | None = None,
    ):
        """Consume messages and invoke callback for each."""
        consumed = 0
        try:
            while max_messages is None or consumed < max_messages:
                msg = self.consumer.poll(timeout)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error("Consumer error: %s", msg.error())
                    continue

                try:
                    topic = msg.topic()
                    key = msg.key().decode("utf-8") if msg.key() else None
                    value = json.loads(msg.value().decode("utf-8"))
                    callback(topic, value)
                    consumed += 1
                except json.JSONDecodeError as e:
                    logger.error("Failed to decode message: %s", e)
                except Exception as e:
                    logger.error("Error processing message: %s", e)
        except KeyboardInterrupt:
            logger.info("Consumer interrupted")
        finally:
            self.close()

    def consume_once(self, topic: str, timeout: float = 5.0) -> dict[str, Any] | None:
        """Consume a single message from a topic."""
        self.consumer.subscribe([topic])
        msg = self.consumer.poll(timeout)
        if msg and not msg.error():
            return json.loads(msg.value().decode("utf-8"))
        return None

    def close(self):
        """Close the consumer."""
        if self._consumer:
            self._consumer.close()
            self._consumer = None


def create_topics(bootstrap_servers: str | None = None, num_partitions: int = 3):
    """Create all required Kafka topics."""
    servers = bootstrap_servers or config.KAFKA_BOOTSTRAP_SERVERS
    admin = AdminClient({"bootstrap.servers": servers})

    new_topics = [
        NewTopic(topic, num_partitions=num_partitions, replication_factor=1)
        for topic in KAFKA_TOPICS.values()
    ]

    futures = admin.create_topics(new_topics)
    for topic, future in futures.items():
        try:
            future.result()
            logger.info("Created topic: %s", topic)
        except KafkaException as e:
            if e.args[0].code() == KafkaError.TOPIC_ALREADY_EXISTS:
                logger.debug("Topic already exists: %s", topic)
            else:
                logger.error("Failed to create topic %s: %s", topic, e)
