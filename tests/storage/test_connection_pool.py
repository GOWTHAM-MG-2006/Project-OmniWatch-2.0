import pytest
from storage.connection_pool import ConnectionPoolManager


class TestConnectionPoolManager:
    def test_clickhouse_pool_exists(self):
        manager = ConnectionPoolManager()
        assert manager.clickhouse is not None

    def test_redis_pool_exists(self):
        manager = ConnectionPoolManager()
        assert manager.redis is not None

    def test_get_pool_stats(self):
        manager = ConnectionPoolManager()
        stats = manager.get_pool_stats()
        assert "clickhouse" in stats
        assert "redis" in stats
