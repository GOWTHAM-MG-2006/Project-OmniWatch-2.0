"""
OmniWatch 2.0 — NexusStore
Component: Graph Store (Apache Kuzu)
Layer: 4
Phase: 1
Purpose: Embedded graph database client for causal knowledge graph
Inputs: Topology updates from TopoBrain
Outputs: Graph queries for AI causal analysis and blast radius
"""

import os
import json
import logging
from typing import Any

import kuzu

logger = logging.getLogger(__name__)

# Node type definitions from AGENTS.md
NODE_TYPES = {
    "Service": ["id", "name", "type", "criticality", "cloud_provider", "status", "anomaly_score", "last_seen"],
    "Process": ["id", "name", "type", "container_id", "pod_id", "host_id", "anomaly_score"],
    "Host": ["id", "name", "type", "cloud_provider", "region", "cpu", "memory", "anomaly_score"],
    "Infrastructure": ["id", "name", "type", "cloud_provider", "status", "anomaly_score"],
    "Database": ["id", "name", "type", "cloud_provider", "status", "anomaly_score"],
    "GenAIService": ["id", "name", "model", "provider", "token_cost", "latency", "anomaly_score"],
    "BusinessTransaction": ["id", "name", "revenue_impact", "sla_target", "error_budget"],
    "CostCenter": ["id", "name", "hourly_cost_usd", "carbon_grams_per_hour"],
}

# Relationship type definitions from AGENTS.md
RELATIONSHIP_TYPES = {
    "CALLS": ["latency_p50", "latency_p95", "latency_p99", "error_rate"],
    "READS_FROM": ["query_type", "avg_duration_ms"],
    "DEPENDS_ON": ["dependency_type", "criticality"],
    "DEPLOYED_ON": ["deployment_version", "deployed_at"],
    "HOSTED_BY": ["cost_center_id", "hourly_cost"],
    "INFERRED_BY": ["causal_score", "confidence", "method"],
}


class GraphStore:
    """Apache Kuzu embedded graph database client."""

    def __init__(self, database_path: str | None = None):
        self.db_path = database_path or os.getenv("KUZU_DATABASE_PATH", "./data/omniwatch-graph")
        self._db = None
        self._conn = None

    @property
    def db(self):
        if self._db is None:
            os.makedirs(self.db_path, exist_ok=True)
            self._db = kuzu.Database(self.db_path)
        return self._db

    @property
    def conn(self):
        if self._conn is None:
            self._conn = kuzu.Connection(self.db)
        return self._conn

    def initialize_schema(self):
        """Create all node and relationship tables."""
        # Create node tables
        for node_type, props in NODE_TYPES.items():
            prop_defs = []
            for prop in props:
                if prop == "id":
                    prop_defs.append(f"{prop} STRING PRIMARY KEY")
                elif prop in ("anomaly_score", "cpu", "memory", "token_cost", "latency",
                              "revenue_impact", "error_budget", "hourly_cost_usd",
                              "carbon_grams_per_hour", "hourly_cost"):
                    prop_defs.append(f"{prop} DOUBLE")
                elif prop in ("criticality",):
                    prop_defs.append(f"{prop} STRING")
                else:
                    prop_defs.append(f"{prop} STRING")

            query = f"CREATE NODE TABLE IF NOT EXISTS {node_type} ({', '.join(prop_defs)})"
            try:
                self.conn.execute(query)
                logger.info("Created node table: %s", node_type)
            except Exception as e:
                logger.debug("Node table %s may already exist: %s", node_type, e)

        # Create relationship tables
        for rel_type, props in RELATIONSHIP_TYPES.items():
            prop_defs = []
            for prop in props:
                if prop in ("latency_p50", "latency_p95", "latency_p99", "error_rate",
                            "avg_duration_ms", "causal_score", "confidence", "hourly_cost"):
                    prop_defs.append(f"{prop} DOUBLE")
                else:
                    prop_defs.append(f"{prop} STRING")

            # Create generic FROM/TO relationship (specific source/target set at query time)
            query = f"""CREATE REL TABLE IF NOT EXISTS {rel_type}
                (FROM Service TO Service, FROM Service TO Process, FROM Service TO Host,
                 FROM Service TO Database, FROM Service TO GenAIService,
                 FROM Process TO Host, FROM Host TO Infrastructure,
                 FROM Database TO Host, FROM GenAIService TO Service,
                 FROM BusinessTransaction TO Service, FROM CostCenter TO Host,
                 {', '.join(prop_defs)})"""
            try:
                self.conn.execute(query)
                logger.info("Created relationship table: %s", rel_type)
            except Exception as e:
                logger.debug("Rel table %s may already exist: %s", rel_type, e)

    def create_node(self, node_type: str, properties: dict[str, Any]) -> bool:
        """Create a node of the specified type."""
        if node_type not in NODE_TYPES:
            raise ValueError(f"Unknown node type: {node_type}")

        props = NODE_TYPES[node_type]
        prop_names = ", ".join(props)
        prop_values = ", ".join([f"'{properties.get(p, '')}'" for p in props])

        query = f"CREATE (n:{node_type} {{ {prop_names} := {prop_values} }})"
        try:
            self.conn.execute(query)
            return True
        except Exception as e:
            logger.error("Failed to create %s node: %s", node_type, e)
            return False

    def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Create a relationship between two nodes."""
        if rel_type not in RELATIONSHIP_TYPES:
            raise ValueError(f"Unknown relationship type: {rel_type}")

        props = properties or {}
        prop_str = ""
        if props:
            prop_parts = []
            for k, v in props.items():
                if isinstance(v, str):
                    prop_parts.append(f"{k}: '{v}'")
                else:
                    prop_parts.append(f"{k}: {v}")
            prop_str = " {" + ", ".join(prop_parts) + "}"

        query = f"""
        MATCH (a:Service), (b:Service)
        WHERE a.id = '{from_id}' AND b.id = '{to_id}'
        CREATE (a)-[:{rel_type}{prop_str}]->(b)
        """
        try:
            self.conn.execute(query)
            return True
        except Exception as e:
            logger.error("Failed to create relationship %s: %s", rel_type, e)
            return False

    def get_node(self, node_type: str, node_id: str) -> dict[str, Any] | None:
        """Get a node by ID."""
        query = f"MATCH (n:{node_type}) WHERE n.id = '{node_id}' RETURN n.*"
        try:
            result = self.conn.execute(query)
            if result.has_next():
                row = result.get_next()
                return {col: row[i] for i, col in enumerate(result.get_column_names())}
            return None
        except Exception as e:
            logger.error("Failed to get node %s:%s — %s", node_type, node_id, e)
            return None

    def query_neighbors(self, node_id: str, direction: str = "both", rel_type: str | None = None) -> list[dict[str, Any]]:
        """Query neighbors of a node."""
        rel_clause = f":{rel_type}" if rel_type else ""

        if direction == "out":
            query = f"MATCH (a:Service)-[{rel_clause}]->(b) WHERE a.id = '{node_id}' RETURN b.*"
        elif direction == "in":
            query = f"MATCH (a)-[{rel_clause}]->(b:Service) WHERE b.id = '{node_id}' RETURN a.*"
        else:
            query = f"MATCH (a:Service)-[{rel_clause}]-(b) WHERE a.id = '{node_id}' RETURN b.*"

        try:
            result = self.conn.execute(query)
            neighbors = []
            while result.has_next():
                row = result.get_next()
                neighbors.append({col: row[i] for i, col in enumerate(result.get_column_names())})
            return neighbors
        except Exception as e:
            logger.error("Failed to query neighbors for %s: %s", node_id, e)
            return []

    def shortest_path(self, from_id: str, to_id: str) -> list[dict[str, Any]]:
        """Find shortest path between two nodes."""
        query = f"""
        MATCH (a:Service), (b:Service),
              path = shortestPath((a)-[*]-(b))
        WHERE a.id = '{from_id}' AND b.id = '{to_id}'
        RETURN path
        """
        try:
            result = self.conn.execute(query)
            paths = []
            while result.has_next():
                row = result.get_next()
                paths.append({"path": row[0]})
            return paths
        except Exception as e:
            logger.error("Failed to find shortest path: %s", e)
            return []

    def update_anomaly_score(self, node_type: str, node_id: str, score: float) -> bool:
        """Update the anomaly score for a node."""
        query = f"MATCH (n:{node_type}) WHERE n.id = '{node_id}' SET n.anomaly_score = {score}"
        try:
            self.conn.execute(query)
            return True
        except Exception as e:
            logger.error("Failed to update anomaly score: %s", e)
            return False

    def get_all_nodes(self, node_type: str, limit: int = 1000) -> list[dict[str, Any]]:
        """Get all nodes of a type."""
        query = f"MATCH (n:{node_type}) RETURN n.* LIMIT {limit}"
        try:
            result = self.conn.execute(query)
            nodes = []
            while result.has_next():
                row = result.get_next()
                nodes.append({col: row[i] for i, col in enumerate(result.get_column_names())})
            return nodes
        except Exception as e:
            logger.error("Failed to get all %s nodes: %s", node_type, e)
            return []

    def delete_node(self, node_type: str, node_id: str) -> bool:
        """Delete a node and its relationships."""
        query = f"MATCH (n:{node_type}) WHERE n.id = '{node_id}' DETACH DELETE n"
        try:
            self.conn.execute(query)
            return True
        except Exception as e:
            logger.error("Failed to delete node: %s", e)
            return False
