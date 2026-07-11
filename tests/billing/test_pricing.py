"""Tests for OmniWatch 2.0 Pricing Engine."""
import sys
from pathlib import Path
import importlib.util

# Force-import billing.pricing_engine from project root to avoid
# tests/billing/__init__.py namespace collision.
_root = Path(__file__).resolve().parent.parent.parent
_spec = importlib.util.spec_from_file_location(
    "billing.pricing_engine", str(_root / "billing" / "pricing_engine.py")
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["billing.pricing_engine"] = _mod
_spec.loader.exec_module(_mod)

import pytest
from billing.pricing_engine import PricingEngine


class TestPricingEngine:
    def test_free_tier_limits(self):
        engine = PricingEngine()
        tier = engine.get_tier("free")
        assert tier.events_limit == 1_000_000

    def test_calculate_cost_within_limits(self):
        engine = PricingEngine()
        cost = engine.calculate_cost(tier="free", events_used=500_000, queries_used=50, storage_used_gb=0.5)
        assert cost.total == 0.0

    def test_calculate_cost_over_events_limit(self):
        engine = PricingEngine()
        cost = engine.calculate_cost(tier="free", events_used=1_500_000, queries_used=50, storage_used_gb=0.5)
        assert cost.total > 0
        assert cost.overage_events > 0

    def test_starter_tier_cost(self):
        engine = PricingEngine()
        cost = engine.calculate_cost(tier="starter", events_used=5_000_000, queries_used=500, storage_used_gb=5)
        assert cost.base_price == 49.0
        assert cost.total == 49.0

    def test_pro_tier_overage(self):
        engine = PricingEngine()
        cost = engine.calculate_cost(tier="pro", events_used=150_000_000, queries_used=10_000, storage_used_gb=100)
        assert cost.total > 199.0
