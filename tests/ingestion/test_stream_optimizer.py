import pytest
from ingestion.stream_forge.stream_optimizer import StreamOptimizer


class TestStreamOptimizer:
    def test_batch_entity_resolution(self):
        optimizer = StreamOptimizer()
        entities = [{"id": f"e{i}", "name": f"entity_{i}"} for i in range(10)]
        result = optimizer.batch_entity_resolution(entities)
        assert len(result) == 10

    def test_async_pii_detection(self):
        optimizer = StreamOptimizer()
        result = optimizer.async_pii_detection("user@email.com")
        assert result is not None
