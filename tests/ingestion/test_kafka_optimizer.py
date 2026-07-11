"""Tests for OmniWatch 2.0 Kafka Optimizer."""
import sys
from pathlib import Path
import importlib.util

# Force-import ingestion.stream_forge.kafka_optimizer from project root
_root = Path(__file__).resolve().parent.parent.parent
_spec = importlib.util.spec_from_file_location(
    "ingestion.stream_forge.kafka_optimizer",
    str(_root / "ingestion" / "stream_forge" / "kafka_optimizer.py"),
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["ingestion.stream_forge.kafka_optimizer"] = _mod
_spec.loader.exec_module(_mod)

import pytest
from ingestion.stream_forge.kafka_optimizer import KafkaOptimizer


class TestKafkaOptimizer:
    def test_get_optimized_producer_config(self):
        optimizer = KafkaOptimizer()
        config = optimizer.get_optimized_producer_config()
        assert "batch.size" in config
        assert "linger.ms" in config
        assert "compression.type" in config

    def test_get_optimized_consumer_config(self):
        optimizer = KafkaOptimizer()
        config = optimizer.get_optimized_consumer_config()
        assert "max.poll.records" in config
        assert "fetch.min.bytes" in config

    def test_monitor_topic_lag(self):
        optimizer = KafkaOptimizer()
        lag = optimizer.monitor_topic_lag("test_topic")
        assert isinstance(lag, dict)