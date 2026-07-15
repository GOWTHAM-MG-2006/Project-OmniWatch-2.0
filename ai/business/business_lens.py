"""
OmniWatch 2.0 — BusinessLens
Component: BusinessLens
Layer: AI (Business)
Phase: 7
Purpose: Maps IT anomalies to business transactions
Inputs: Incidents, service metrics, transaction data
Outputs: Business impact analysis, revenue impact estimates
"""

import os
import json
from dataclasses import dataclass
from typing import Optional


class BusinessLens:
    """Business impact correlation with configurable service mappings."""

    DEFAULT_REVENUE = json.loads(os.environ.get("SERVICE_REVENUE_CONFIG", '{"payment-service": 150, "checkout-service": 120, "order-service": 100, "inventory-service": 50}'))
    DEFAULT_TXNS = json.loads(os.environ.get("SERVICE_TXN_CONFIG", '{"payment-service": 500, "checkout-service": 300, "order-service": 200, "inventory-service": 100}'))

    def __init__(self, kuzu_client=None):
        self._kuzu = kuzu_client
        self._revenue_cache = {}
        self._txn_cache = {}

    def _get_service_config(self, service: str) -> tuple[float, float]:
        """Get revenue and transaction config for a service."""
        if service in self._revenue_cache:
            return self._revenue_cache[service], self._txn_cache.get(service, 1000)

        if self._kuzu:
            try:
                query = f"MATCH (n:BusinessTransaction {{name: '{service}'}}) RETURN n.revenue_impact, n.transactions_per_hour"
                results = self._kuzu.execute(query)
                if results:
                    rev = results[0].get("revenue_impact", 0.01)
                    txns = results[0].get("transactions_per_hour", 1000)
                    self._revenue_cache[service] = rev
                    self._txn_cache[service] = txns
                    return rev, txns
            except Exception:
                pass

        return self.DEFAULT_REVENUE.get(service, 0.01), self.DEFAULT_TXNS.get(service, 1000)

    def correlate_incident(self, incident_id, affected_services, error_rate):
        total_revenue_impact = 0.0
        total_affected_users = 0
        for service in affected_services:
            rev_per_txn, txns_per_hour = self._get_service_config(service)
            affected_txns = txns_per_hour * error_rate
            total_revenue_impact += affected_txns * rev_per_txn
            total_affected_users += int(affected_txns)
        return {
            "incident_id": incident_id, "affected_services": affected_services,
            "estimated_revenue_impact": round(total_revenue_impact, 2),
            "affected_users": total_affected_users,
            "sla_breach": error_rate > 0.01,
            "cost_per_hour": round(total_revenue_impact, 2),
        }

    def calculate_cost_per_transaction(self, service, total_cost_usd, total_transactions):
        if total_transactions == 0:
            return 0.0
        return round(total_cost_usd / total_transactions, 6)
