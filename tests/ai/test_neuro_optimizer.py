import pytest
from ai.performance.neuro_optimizer import NeuroOptimizer


class TestNeuroOptimizer:
    def test_cache_baselines(self):
        optimizer = NeuroOptimizer()
        result = optimizer.cache_baselines({"cpu": [0.1, 0.2, 0.3]})
        assert result is True

    def test_batch_anomaly_detection(self):
        optimizer = NeuroOptimizer()
        entities = [{"entity_id": f"e{i}", "metrics": [0.1]} for i in range(10)]
        result = optimizer.batch_anomaly_detection(entities)
        assert len(result) == 10

    def test_cache_graph_traversal(self):
        optimizer = NeuroOptimizer()
        result = optimizer.cache_graph_traversal("entity_1", {"path": ["a", "b"]})
        assert result is True
