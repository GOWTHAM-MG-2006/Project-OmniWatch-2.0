import pytest
from storage.cache_layer import CacheLayer


class TestCacheLayer:
    def test_set_and_get(self):
        cache = CacheLayer()
        cache.set("key1", "value1", ttl=30)
        result = cache.get("key1")
        assert result == "value1"

    def test_invalidate(self):
        cache = CacheLayer()
        cache.set("key2", "value2", ttl=30)
        cache.invalidate("key2")
        result = cache.get("key2")
        assert result is None

    def test_get_hit_rate(self):
        cache = CacheLayer()
        cache.set("key3", "value3", ttl=30)
        cache.get("key3")
        cache.get("key3")
        rate = cache.get_hit_rate()
        assert rate >= 0
