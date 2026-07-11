"""
OmniWatch 2.0 — Integration Tests (Message Queue)
Component: Message Queue Integration Tests
Layer: Integration
Phase: 7
Purpose: Unit tests for RabbitMQ, NATS, and Pulsar integrations
Inputs: N/A
Outputs: Test results
"""

import pytest

from integrations.library.message_queue.rabbitmq import RabbitMQIntegration
from integrations.library.message_queue.nats import NATSIntegration
from integrations.library.message_queue.pulsar import PulsarIntegration


class TestRabbitMQ:
    def test_collect_metrics(self):
        integration = RabbitMQIntegration(config={"RABBITMQ_HOST": "localhost"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) == 6

    def test_metric_structure(self):
        integration = RabbitMQIntegration(config={"RABBITMQ_HOST": "localhost"})
        metrics = integration.collect_metrics()
        for metric in metrics:
            assert "name" in metric
            assert "value" in metric
            assert "timestamp" in metric
            assert "labels" in metric

    def test_metric_names(self):
        integration = RabbitMQIntegration(config={"RABBITMQ_HOST": "localhost"})
        metrics = integration.collect_metrics()
        names = [m["name"] for m in metrics]
        assert "rabbitmq_queue_depth" in names
        assert "rabbitmq_messages_total" in names
        assert "rabbitmq_consumers" in names
        assert "rabbitmq_connections" in names

    def test_health_check_success(self):
        integration = RabbitMQIntegration(config={"RABBITMQ_HOST": "localhost"})
        assert integration.health_check() is True

    def test_health_check_failure(self):
        integration = RabbitMQIntegration(config={})
        assert integration.health_check() is False

    def test_host_label(self):
        integration = RabbitMQIntegration(config={"RABBITMQ_HOST": "rmq-prod-01"})
        metrics = integration.collect_metrics()
        host_labels = [m["labels"]["host"] for m in metrics]
        assert all(h == "rmq-prod-01" for h in host_labels)


class TestNATS:
    def test_collect_metrics(self):
        integration = NATSIntegration(config={"NATS_URL": "nats://localhost:4222"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) == 6

    def test_metric_structure(self):
        integration = NATSIntegration(config={"NATS_URL": "nats://localhost:4222"})
        metrics = integration.collect_metrics()
        for metric in metrics:
            assert "name" in metric
            assert "value" in metric
            assert "timestamp" in metric
            assert "labels" in metric

    def test_metric_names(self):
        integration = NATSIntegration(config={"NATS_URL": "nats://localhost:4222"})
        metrics = integration.collect_metrics()
        names = [m["name"] for m in metrics]
        assert "nats_connections" in names
        assert "nats_messages_in" in names
        assert "nats_messages_out" in names
        assert "nats_subscriptions" in names

    def test_health_check_success(self):
        integration = NATSIntegration(config={"NATS_URL": "nats://localhost:4222"})
        assert integration.health_check() is True

    def test_health_check_failure(self):
        integration = NATSIntegration(config={})
        assert integration.health_check() is False

    def test_url_label(self):
        integration = NATSIntegration(config={"NATS_URL": "nats://nats-cluster:4222"})
        metrics = integration.collect_metrics()
        url_labels = [m["labels"]["url"] for m in metrics]
        assert all(u == "nats://nats-cluster:4222" for u in url_labels)


class TestPulsar:
    def test_collect_metrics(self):
        integration = PulsarIntegration(config={"PULSAR_URL": "pulsar://localhost:6650"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) == 7

    def test_metric_structure(self):
        integration = PulsarIntegration(config={"PULSAR_URL": "pulsar://localhost:6650"})
        metrics = integration.collect_metrics()
        for metric in metrics:
            assert "name" in metric
            assert "value" in metric
            assert "timestamp" in metric
            assert "labels" in metric

    def test_metric_names(self):
        integration = PulsarIntegration(config={"PULSAR_URL": "pulsar://localhost:6650"})
        metrics = integration.collect_metrics()
        names = [m["name"] for m in metrics]
        assert "pulsar_topic_throughput" in names
        assert "pulsar_consumers" in names
        assert "pulsar_consumer_lag" in names
        assert "pulsar_storage_size" in names

    def test_health_check_success(self):
        integration = PulsarIntegration(config={"PULSAR_URL": "pulsar://localhost:6650"})
        assert integration.health_check() is True

    def test_health_check_failure(self):
        integration = PulsarIntegration(config={})
        assert integration.health_check() is False

    def test_url_label(self):
        integration = PulsarIntegration(config={"PULSAR_URL": "pulsar://pulsar-broker:6650"})
        metrics = integration.collect_metrics()
        url_labels = [m["labels"]["url"] for m in metrics]
        assert all(u == "pulsar://pulsar-broker:6650" for u in url_labels)
