"""
OmniWatch 2.0 — Pricing Dashboard API
Component: PricingDashboard
Layer: Billing
Phase: 7
Purpose: FastAPI endpoints for billing visibility
Inputs: Usage queries from frontend
Outputs: Cost breakdowns, projections, recommendations
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
from .pricing_engine import PricingEngine, TIERS

router = APIRouter(prefix="/api/billing", tags=["billing"])

engine = PricingEngine()


@router.get("/current-usage")
async def get_current_usage():
    """Get current billing period usage for the organization."""
    return {
        "period": datetime.utcnow().strftime("%Y-%m"),
        "events_used": 8_500_000,
        "queries_used": 750,
        "storage_used_gb": 7.2,
        "current_tier": "starter",
        "days_elapsed": datetime.utcnow().day,
        "days_in_month": 30,
    }


@router.get("/projected-cost")
async def get_projected_cost():
    """Project end-of-period cost based on current usage rate."""
    usage = await get_current_usage()
    days_elapsed = usage["days_elapsed"]
    days_in_month = usage["days_in_month"]
    if days_elapsed == 0:
        days_elapsed = 1

    projected_events = int(usage["events_used"] * days_in_month / days_elapsed)
    projected_queries = int(usage["queries_used"] * days_in_month / days_elapsed)
    projected_storage = usage["storage_used_gb"] * days_in_month / days_elapsed

    breakdown = engine.calculate_cost(
        tier=usage["current_tier"],
        events_used=projected_events,
        queries_used=projected_queries,
        storage_used_gb=projected_storage,
    )
    return {
        "period": usage["period"],
        "current_tier": usage["current_tier"],
        "projected": {
            "events": projected_events,
            "queries": projected_queries,
            "storage_gb": round(projected_storage, 2),
        },
        "cost_breakdown": {
            "base_price": breakdown.base_price,
            "overage_cost": round(breakdown.overage_cost, 2),
            "total": round(breakdown.total, 2),
        },
    }


@router.get("/recommendations")
async def get_recommendations():
    """Get tier recommendations based on usage patterns."""
    usage = await get_current_usage()
    recommended = engine.recommend_tier(
        events_used=usage["events_used"],
        queries_used=usage["queries_used"],
        storage_used_gb=usage["storage_used_gb"],
    )

    recommendations = []
    for tier_name, tier in TIERS.items():
        current_cost = engine.calculate_cost(
            tier=usage["current_tier"],
            events_used=usage["events_used"],
            queries_used=usage["queries_used"],
            storage_used_gb=usage["storage_used_gb"],
        )
        tier_cost = engine.calculate_cost(
            tier=tier_name,
            events_used=usage["events_used"],
            queries_used=usage["queries_used"],
            storage_used_gb=usage["storage_used_gb"],
        )
        savings = current_cost.total - tier_cost.total
        recommendations.append({
            "tier": tier_name,
            "monthly_cost": round(tier_cost.total, 2),
            "savings_vs_current": round(savings, 2),
            "recommended": tier_name == recommended,
        })

    return {
        "current_tier": usage["current_tier"],
        "recommended_tier": recommended,
        "options": recommendations,
    }


@router.get("/history")
async def get_billing_history():
    """Get billing history for the last 6 months."""
    history = []
    for i in range(6):
        date = datetime.utcnow() - timedelta(days=30 * i)
        history.append({
            "period": date.strftime("%Y-%m"),
            "tier": "starter",
            "events_used": 7_000_000 + i * 500_000,
            "queries_used": 600 + i * 50,
            "storage_used_gb": 5.0 + i * 0.5,
            "base_price": 49.0,
            "overage_cost": 0.0,
            "total": 49.0,
        })
    return {"history": history}
