"""
OmniWatch 2.0 — TopoBrain
Component: Graph Database
Layer: 5
Phase: 1
Purpose: TopoBrain graph operations using Apache Kuzu for 8-layer causal knowledge graph
Inputs: Topology updates from StreamForge
Outputs: Graph queries for causal analysis, blast radius, dependency chains
"""

import os
import json
import logging
from typing import Any
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.graph_store import GraphStore, NODE_TYPES, RELATIONSHIP_TYPES

logger = logging.getLogger(__name__)


class TopoBrainGraph:
    """TopoBrain graph operations for the 8-layer causal knowledge graph."""

    def __init__(self, database_path: str | None = None):
        self.store = GraphStore(database_path)

    def initialize(self):
        """Initialize the graph schema."""
        self.store.initialize_schema()
        logger.info("TopoBrain graph schema initialized")

    def add_service(
        self,
        service_id: str,
        name: str,
        service_type: str = "microservice",
        criticality: str = "medium",
        cloud_provider: str = "local",
        status: str = "healthy",
        anomaly_score: float = 0.0,
    ) -> bool:
        """Add a Service node."""
        return self.store.create_node("Service", {
            "id": service_id,
            "name": name,
            "type": service_type,
            "criticality": criticality,
            "cloud_provider": cloud_provider,
            "status": status,
            "anomaly_score": str(anomaly_score),
            "last_seen": datetime.utcnow().isoformat(),
        })

    def add_host(
        self,
        host_id: str,
        name: str,
        host_type: str = "vm",
        cloud_provider: str = "local",
        region: str = "us-east-1",
        cpu: float = 0.0,
        memory: float = 0.0,
        anomaly_score: float = 0.0,
    ) -> bool:
        """Add a Host node."""
        return self.store.create_node("Host", {
            "id": host_id,
            "name": name,
            "type": host_type,
            "cloud_provider": cloud_provider,
            "region": region,
            "cpu": str(cpu),
            "memory": str(memory),
            "anomaly_score": str(anomaly_score),
        })

    def add_database(
        self,
        db_id: str,
        name: str,
        db_type: str = "postgresql",
        cloud_provider: str = "local",
        status: str = "healthy",
        anomaly_score: float = 0.0,
    ) -> bool:
        """Add a Database node."""
        return self.store.create_node("Database", {
            "id": db_id,
            "name": name,
            "type": db_type,
            "cloud_provider": cloud_provider,
            "status": status,
            "anomaly_score": str(anomaly_score),
        })

    def add_process(
        self,
        process_id: str,
        name: str,
        process_type: str = "application",
        container_id: str = "",
        pod_id: str = "",
        host_id: str = "",
        anomaly_score: float = 0.0,
    ) -> bool:
        """Add a Process node."""
        return self.store.create_node("Process", {
            "id": process_id,
            "name": name,
            "type": process_type,
            "container_id": container_id,
            "pod_id": pod_id,
            "host_id": host_id,
            "anomaly_score": str(anomaly_score),
        })

    def add_genai_service(
        self,
        service_id: str,
        name: str,
        model: str = "",
        provider: str = "",
        token_cost: float = 0.0,
        latency: float = 0.0,
        anomaly_score: float = 0.0,
    ) -> bool:
        """Add a GenAI Service node."""
        return self.store.create_node("GenAIService", {
            "id": service_id,
            "name": name,
            "model": model,
            "provider": provider,
            "token_cost": str(token_cost),
            "latency": str(latency),
            "anomaly_score": str(anomaly_score),
        })

    def add_infrastructure(
        self,
        infra_id: str,
        name: str,
        infra_type: str = "kubernetes",
        cloud_provider: str = "local",
        status: str = "healthy",
        anomaly_score: float = 0.0,
    ) -> bool:
        """Add an Infrastructure node."""
        return self.store.create_node("Infrastructure", {
            "id": infra_id,
            "name": name,
            "type": infra_type,
            "cloud_provider": cloud_provider,
            "status": status,
            "anomaly_score": str(anomaly_score),
        })

    def add_business_transaction(
        self,
        txn_id: str,
        name: str,
        revenue_impact: float = 0.0,
        sla_target: str = "99.9",
        error_budget: str = "0.1",
    ) -> bool:
        """Add a Business Transaction node."""
        return self.store.create_node("BusinessTransaction", {
            "id": txn_id,
            "name": name,
            "revenue_impact": str(revenue_impact),
            "sla_target": sla_target,
            "error_budget": error_budget,
        })

    def add_cost_center(
        self,
        center_id: str,
        name: str,
        hourly_cost_usd: float = 0.0,
        carbon_grams_per_hour: float = 0.0,
    ) -> bool:
        """Add a Cost Center node."""
        return self.store.create_node("CostCenter", {
            "id": center_id,
            "name": name,
            "hourly_cost_usd": str(hourly_cost_usd),
            "carbon_grams_per_hour": str(carbon_grams_per_hour),
        })

    def add_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Add a relationship between two nodes."""
        return self.store.create_relationship(from_id, to_id, rel_type, properties)

    def get_dependencies(self, service_id: str) -> list[dict[str, Any]]:
        """Get all dependencies of a service (what it calls/reads from)."""
        return self.store.query_neighbors(service_id, direction="out")

    def get_dependents(self, service_id: str) -> list[dict[str, Any]]:
        """Get all services that depend on this service."""
        return self.store.query_neighbors(service_id, direction="in")

    def update_anomaly_score(self, node_type: str, node_id: str, score: float) -> bool:
        """Update the anomaly score for a node."""
        return self.store.update_anomaly_score(node_type, node_id, score)

    def get_entity(self, node_type: str, entity_id: str) -> dict[str, Any] | None:
        """Get an entity by type and ID."""
        return self.store.get_node(node_type, entity_id)

    def get_all_services(self, limit: int = 1000) -> list[dict[str, Any]]:
        """Get all services in the graph."""
        return self.store.get_all_nodes("Service", limit)

    def get_path_between(self, from_id: str, to_id: str) -> list[dict[str, Any]]:
        """Find the path between two services."""
        return self.store.shortest_path(from_id, to_id)
