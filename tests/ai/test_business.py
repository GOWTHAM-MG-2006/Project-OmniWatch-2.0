import pytest
from ai.business.business_lens import BusinessLens
from ai.business.cost_brain import CostBrain

class TestBusinessLens:
    def test_correlate_incident_to_revenue(self):
        lens = BusinessLens()
        impact = lens.correlate_incident(incident_id="INC-001", affected_services=["payment-api"], error_rate=0.05)
        assert "estimated_revenue_impact" in impact
        assert impact["estimated_revenue_impact"] > 0
    def test_calculate_cost_per_transaction(self):
        lens = BusinessLens()
        cost = lens.calculate_cost_per_transaction("payment-api", 1000, 50000)
        assert cost == 0.02

class TestCostBrain:
    def test_track_entity_cost(self):
        brain = CostBrain()
        cost = brain.track_entity_cost("payment-api", 2.5, "aws")
        assert cost["entity_id"] == "payment-api"
    def test_calculate_carbon_footprint(self):
        brain = CostBrain()
        carbon = brain.calculate_carbon_footprint("payment-api", 2.5, "aws")
        assert "grams_per_hour" in carbon
        assert carbon["grams_per_hour"] > 0
