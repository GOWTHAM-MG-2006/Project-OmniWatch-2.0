"""
OmniWatch 2.0 — CostBrain
Component: CostBrain
Layer: AI (Business)
Phase: 7
Purpose: Real-time cloud cost and carbon tracking per entity
Inputs: Cloud billing data, entity metrics
Outputs: Cost per entity, carbon footprint, cost anomalies
"""

CARBON_INTENSITY = {"aws": 0.42, "azure": 0.39, "gcp": 0.30, "on-premise": 0.50}
PUE = {"aws": 1.2, "azure": 1.18, "gcp": 1.1, "on-premise": 1.6}


class CostBrain:
    def track_entity_cost(self, entity_id, hourly_cost_usd, cloud_provider):
        return {
            "entity_id": entity_id, "hourly_cost_usd": hourly_cost_usd,
            "daily_cost_usd": round(hourly_cost_usd * 24, 2),
            "monthly_cost_usd": round(hourly_cost_usd * 24 * 30, 2),
            "cloud_provider": cloud_provider,
        }

    def calculate_carbon_footprint(self, entity_id, hourly_cost_usd, cloud_provider):
        cost_per_kwh = 0.10
        kwh_per_hour = hourly_cost_usd / cost_per_kwh
        carbon_intensity = CARBON_INTENSITY.get(cloud_provider, 0.42)
        pue = PUE.get(cloud_provider, 1.2)
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
