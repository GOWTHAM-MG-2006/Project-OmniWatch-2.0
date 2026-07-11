"""
OmniWatch 2.0 — BusinessLens
Component: BusinessLens
Layer: AI (Business)
Phase: 7
Purpose: Maps IT anomalies to business transactions
Inputs: Incidents, service metrics, transaction data
Outputs: Business impact analysis, revenue impact estimates
"""

from dataclasses import dataclass
from typing import Optional


class BusinessLens:
    REVENUE_PER_TRANSACTION = {
        "payment-api": 0.50, "checkout-service": 0.75,
        "user-service": 0.01, "inventory-api": 0.25,
    }
    TRANSACTIONS_PER_HOUR = {
        "payment-api": 10000, "checkout-service": 8000,
        "user-service": 50000, "inventory-api": 15000,
    }

    def correlate_incident(self, incident_id, affected_services, error_rate):
        total_revenue_impact = 0.0
        total_affected_users = 0
        for service in affected_services:
            rev_per_txn = self.REVENUE_PER_TRANSACTION.get(service, 0.01)
            txns_per_hour = self.TRANSACTIONS_PER_HOUR.get(service, 1000)
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
