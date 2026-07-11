import pytest
from storage.connection_pool import ConnectionPoolManager


class TestConnectionPoolManager:
    def test_get_clickhouse_config(self):
        manager = ConnectionPoolManager()
        config = manager.get_clickhouse_config()
        assert "min_connections" in config
        assert "max_connections" in config

    def test_get_redis_config(self):
        manager = ConnectionPoolManager()
        config = manager.get_redis_config()
        assert "max_connections" in config
