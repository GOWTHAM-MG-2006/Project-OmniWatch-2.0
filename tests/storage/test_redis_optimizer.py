import pytest
from storage.redis_optimizer import RedisOptimizer


class TestRedisOptimizer:
    def test_pipeline_batch(self):
        optimizer = RedisOptimizer()
        result = optimizer.pipeline_batch([("set", "key1", "val1"), ("set", "key2", "val2")])
        assert isinstance(result, list)

    def test_cache_warming(self):
        optimizer = RedisOptimizer()
        result = optimizer.cache_warming({"entity:1": {"status": "healthy"}})
        assert result == 1

    def test_memory_profile(self):
        optimizer = RedisOptimizer()
        profile = optimizer.memory_profile()
        assert "used_memory" in profile
