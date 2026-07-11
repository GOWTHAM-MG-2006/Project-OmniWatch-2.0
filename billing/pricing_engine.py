"""
OmniWatch 2.0 — Pricing Engine
Component: PricingEngine
Layer: Billing
Phase: 7
Purpose: Usage-based pricing calculation
Inputs: Usage data (events, queries, storage)
Outputs: Cost calculations, tier recommendations
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PricingTier:
    name: str
    base_price: float
    events_limit: int
    queries_limit: int
    storage_limit_gb: float
    overage_price_per_million_events: float = 0.50
    overage_price_per_1k_queries: float = 0.10
    overage_price_per_gb_storage: float = 0.10


@dataclass
class CostBreakdown:
    tier: str
    base_price: float
    events_used: int
    queries_used: int
    storage_used_gb: float
    overage_events: int = 0
    overage_queries: int = 0
    overage_storage_gb: float = 0.0
    overage_cost: float = 0.0
    total: float = 0.0


TIERS = {
    "free": PricingTier(name="free", base_price=0.0, events_limit=1_000_000, queries_limit=100, storage_limit_gb=1.0),
    "starter": PricingTier(name="starter", base_price=49.0, events_limit=10_000_000, queries_limit=1_000, storage_limit_gb=10.0),
    "pro": PricingTier(name="pro", base_price=199.0, events_limit=100_000_000, queries_limit=10_000, storage_limit_gb=100.0),
    "enterprise": PricingTier(name="enterprise", base_price=999.0, events_limit=1_000_000_000, queries_limit=100_000, storage_limit_gb=1_000.0),
}


class PricingEngine:
    def __init__(self, tiers=None):
        self.tiers = tiers or TIERS

    def get_tier(self, tier_name: str) -> PricingTier:
        if tier_name not in self.tiers:
            raise ValueError(f"Unknown tier: {tier_name}")
        return self.tiers[tier_name]

    def calculate_cost(self, tier, events_used, queries_used, storage_used_gb) -> CostBreakdown:
        pricing_tier = self.get_tier(tier)
        overage_events = max(0, events_used - pricing_tier.events_limit)
        overage_queries = max(0, queries_used - pricing_tier.queries_limit)
        overage_storage = max(0.0, storage_used_gb - pricing_tier.storage_limit_gb)
        overage_cost = (
            (overage_events / 1_000_000) * pricing_tier.overage_price_per_million_events
            + (overage_queries / 1_000) * pricing_tier.overage_price_per_1k_queries
            + overage_storage * pricing_tier.overage_price_per_gb_storage
        )
        return CostBreakdown(
            tier=tier, base_price=pricing_tier.base_price,
            events_used=events_used, queries_used=queries_used, storage_used_gb=storage_used_gb,
            overage_events=overage_events, overage_queries=overage_queries, overage_storage_gb=overage_storage,
            overage_cost=overage_cost, total=pricing_tier.base_price + overage_cost,
        )

    def recommend_tier(self, events_used, queries_used, storage_used_gb) -> str:
        for tier_name in ["free", "starter", "pro", "enterprise"]:
            tier = self.get_tier(tier_name)
            if (events_used <= tier.events_limit * 1.2 and
                queries_used <= tier.queries_limit * 1.2 and
                storage_used_gb <= tier.storage_limit_gb * 1.2):
                return tier_name
        return "enterprise"
