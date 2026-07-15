"""
OmniWatch 2.0 — CostBrain
Component: CostBrain
Layer: AI (Business)
Phase: 7
Purpose: Real-time cloud cost and carbon tracking per entity
Inputs: Cloud billing data, entity metrics
Outputs: Cost per entity, carbon footprint, cost anomalies
"""

import os
import logging

from config import config

logger = logging.getLogger(__name__)

DEFAULT_CARBON_INTENSITY = {"aws": 0.42, "azure": 0.39, "gcp": 0.30, "on-premise": 0.50}
DEFAULT_PUE = {"aws": 1.2, "azure": 1.18, "gcp": 1.1, "on-premise": 1.6}
DEFAULT_COST_PER_KWH = config.COST_PER_KWH


class CostBrain:
    def __init__(self, clickhouse_client=None):
        self._client = clickhouse_client

    def _get_cost_per_kwh(self, region: str = "default") -> float:
        """Get cost per kWh from config or default."""
        if self._client:
            try:
                query = "SELECT cost_per_kwh FROM cost_config WHERE region = {region:String} LIMIT 1"
                results = self._client.query(query, parameters={"region": region})
                if results.result_rows:
                    return results.result_rows[0][0]
            except Exception:
                pass
        return DEFAULT_COST_PER_KWH

    def _get_carbon_intensity(self, provider: str) -> float:
        """Get carbon intensity from config or default."""
        if self._client:
            try:
                query = "SELECT carbon_intensity FROM cost_config WHERE provider = {provider:String} LIMIT 1"
                results = self._client.query(query, parameters={"provider": provider})
                if results.result_rows:
                    return results.result_rows[0][0]
            except Exception:
                pass
        return DEFAULT_CARBON_INTENSITY.get(provider, 0.42)

    def track_entity_cost(self, entity_id, hourly_cost_usd, cloud_provider):
        return {
            "entity_id": entity_id, "hourly_cost_usd": hourly_cost_usd,
            "daily_cost_usd": round(hourly_cost_usd * 24, 2),
            "monthly_cost_usd": round(hourly_cost_usd * 24 * 30, 2),
            "cloud_provider": cloud_provider,
        }

    def calculate_carbon_footprint(self, entity_id, hourly_cost_usd, cloud_provider):
        cost_per_kwh = self._get_cost_per_kwh()
        kwh_per_hour = hourly_cost_usd / cost_per_kwh if cost_per_kwh > 0 else 0
        carbon_intensity = self._get_carbon_intensity(cloud_provider)
        pue = DEFAULT_PUE.get(cloud_provider, 1.2)
        grams_per_hour = kwh_per_hour * carbon_intensity * pue
        return {
            "entity_id": entity_id, "grams_per_hour": round(grams_per_hour, 2),
            "kg_per_month": round((grams_per_hour * 24 * 30) / 1000, 2),
            "cloud_provider": cloud_provider,
        }

    def detect_cost_anomaly(self, entity_id, current_cost, baseline_cost, threshold=0.2):
        if baseline_cost == 0:
            return {"entity_id": entity_id, "is_anomaly": False, "deviation_percent": 0}
        deviation = (current_cost - baseline_cost) / baseline_cost
        return {
            "entity_id": entity_id, "current_cost": current_cost,
            "baseline_cost": baseline_cost, "deviation_percent": round(deviation * 100, 2),
            "is_anomaly": abs(deviation) > threshold,
        }
