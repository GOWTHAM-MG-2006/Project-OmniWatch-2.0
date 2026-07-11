import pytest
from storage.query_optimizer import QueryOptimizer


class TestQueryOptimizer:
    def test_analyze_slow_queries(self):
        optimizer = QueryOptimizer()
        result = optimizer.analyze_slow_queries()
        assert isinstance(result, list)

    def test_suggest_indexes(self):
        optimizer = QueryOptimizer()
        result = optimizer.suggest_indexes()
        assert isinstance(result, list)

    def test_cache_query_result(self):
        optimizer = QueryOptimizer()
        result = optimizer.cache_query_result("test_query", [{"col": 1}], ttl=30)
        assert result is True

    def test_get_cached_result(self):
        optimizer = QueryOptimizer()
        optimizer.cache_query_result("test_query_2", [{"col": 2}], ttl=30)
        cached = optimizer.get_cached_result("test_query_2")
        assert cached is not None
