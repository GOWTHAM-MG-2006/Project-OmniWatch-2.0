import pytest
from performance.memory_optimizer import MemoryOptimizer


class TestMemoryOptimizer:
    def test_profile_memory(self):
        optimizer = MemoryOptimizer()
        result = optimizer.profile_memory()
        assert "used_mb" in result

    def test_detect_leaks(self):
        optimizer = MemoryOptimizer()
        result = optimizer.detect_leaks()
        assert isinstance(result, list)

    def test_get_recommendations(self):
        optimizer = MemoryOptimizer()
        result = optimizer.get_recommendations()
        assert isinstance(result, list)
