"""
OmniWatch 2.0 — Pricing Dashboard API
Component: PricingDashboard
Layer: Billing
Phase: 7
Purpose: FastAPI endpoints for billing visibility with real ClickHouse data
Inputs: Usage queries from frontend
Outputs: Cost breakdowns, projections, recommendations
"""

import os
import logging
from fastapi import APIRouter
from datetime import datetime, timedelta
from .pricing_engine import PricingEngine, TIERS

from config import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])

engine = PricingEngine()


def _get_ch_client():
    """Get ClickHouse client for billing queries."""
    try:
        import clickhouse_connect
        return clickhouse_connect.get_client(
            host=config.CLICKHOUSE_HOST,
            port=config.CLICKHOUSE_PORT,
            database="omniwatch",
        )
    except Exception as e:
        logger.warning("ClickHouse not available for billing: %s", e)
        return None


@router.get("/current-usage")
async def get_current_usage():
    """Get current billing period usage from ClickHouse."""
    client = _get_ch_client()
    if not client:
        return {
            "period": datetime.utcnow().strftime("%Y-%m"),
            "events_used": 0,
            "queries_used": 0,
            "storage_used_gb": 0,
            "current_tier": "free",
            "days_elapsed": datetime.utcnow().day,
            "days_in_month": 30,
        }

    try:
        events_query = "SELECT count(*) as cnt FROM metrics WHERE timestamp >= now() - INTERVAL 1 hour"
        events_result = client.query(events_query)
        events = events_result.first_row[0] if events_result.row_count > 0 else 0

        queries_query = "SELECT count(*) as cnt FROM system.query_log WHERE event_time >= now() - INTERVAL 1 hour"
        queries_result = client.query(queries_query)
        queries = queries_result.first_row[0] if queries_result.row_count > 0 else 0

        storage_query = "SELECT formatReadableSize(sum(bytes_on_disk)) as storage FROM system.parts"
        storage_result = client.query(storage_query)
        storage = storage_result.first_row[0] if storage_result.row_count > 0 else "0 B"

        return {
            "period": datetime.utcnow().strftime("%Y-%m"),
            "events_used": events,
            "queries_used": queries,
            "storage_used_gb": storage,
            "current_tier": "free",
            "days_elapsed": datetime.utcnow().day,
            "days_in_month": 30,
        }
    except Exception as e:
        logger.warning("Billing usage query failed: %s", e)
        return {
            "period": datetime.utcnow().strftime("%Y-%m"),
            "events_used": 0,
            "queries_used": 0,
            "storage_used_gb": "0 B",
            "current_tier": "free",
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

    breakdown = engine.calculate_cost(
        tier=usage["current_tier"],
        events_used=projected_events,
        queries_used=projected_queries,
        storage_used_gb=0,
    )
    return {
        "period": usage["period"],
        "current_tier": usage["current_tier"],
        "projected": {
            "events": projected_events,
            "queries": projected_queries,
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
        storage_used_gb=0,
    )

    recommendations = []
    for tier_name, tier in TIERS.items():
        current_cost = engine.calculate_cost(
            tier=usage["current_tier"],
            events_used=usage["events_used"],
            queries_used=usage["queries_used"],
            storage_used_gb=0,
        )
        tier_cost = engine.calculate_cost(
            tier=tier_name,
            events_used=usage["events_used"],
            queries_used=usage["queries_used"],
            storage_used_gb=0,
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
async def get_billing_history(months: int = 6):
    """Get billing history from ClickHouse cost_carbon table."""
    client = _get_ch_client()
    if not client:
        return {"history": []}

    try:
        query = """
            SELECT
                toStartOfMonth(timestamp) as month,
                sum(hourly_cost_usd) as total_cost,
                sum(carbon_grams_per_hour) as total_carbon
            FROM cost_carbon
            WHERE timestamp >= now() - INTERVAL {m:UInt32} month
            GROUP BY month
            ORDER BY month
        """
        result = client.query(query, parameters={"m": months})
        history = [
            {"month": str(row[0]), "cost_usd": row[1] or 0, "carbon_grams": row[2] or 0}
            for row in result.result_rows
        ]
        return {"history": history}
    except Exception as e:
        logger.warning("Billing history query failed: %s", e)
        return {"history": []}
