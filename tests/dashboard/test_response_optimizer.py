"""Tests for OmniWatch 2.0 Response Optimizer."""
import sys
from pathlib import Path
import importlib.util

# Force-import response_optimizer from project root to avoid
# tests/dashboard/__init__.py namespace collision.
_root = Path(__file__).resolve().parent.parent.parent
_spec = importlib.util.spec_from_file_location(
    "dashboard.backend.performance.response_optimizer",
    str(_root / "dashboard" / "backend" / "performance" / "response_optimizer.py"),
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["dashboard.backend.performance.response_optimizer"] = _mod
_spec.loader.exec_module(_mod)

import pytest
from dashboard.backend.performance.response_optimizer import ResponseOptimizer


class TestResponseOptimizer:
    def test_cache_response(self):
        optimizer = ResponseOptimizer()
        result = optimizer.cache_response("/api/test", {"data": "value"}, ttl=30)
        assert result is True

    def test_get_cached_response(self):
        optimizer = ResponseOptimizer()
        optimizer.cache_response("/api/test2", {"data": "cached"}, ttl=30)
        cached = optimizer.get_cached_response("/api/test2")
        assert cached is not None

    def test_add_pagination(self):
        optimizer = ResponseOptimizer()
        items = list(range(100))
        result = optimizer.add_pagination(items, page=1, page_size=10)
        assert len(result["items"]) == 10
        assert result["total"] == 100
