"""OmniWatch 2.0 — TopologyService: Real-time graph queries from Kuzu."""

import os
import logging
from typing import Any, Optional

from config import config

logger = logging.getLogger(__name__)


class TopologyService:
    """Queries real topology from Kuzu graph database."""

    def __init__(self):
        self._db = None
        self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            try:
                import kuzu
                db_path = os.getenv("KUZU_DATABASE_PATH", "./data/omniwatch-graph")
                self._db = kuzu.Database(db_path)
                self._conn = kuzu.Connection(self._db)
            except Exception as e:
                logger.warning("Kuzu not available: %s", e)
                self._conn = None
        return self._conn

    def _execute(self, query: str, params: dict = None) -> list[dict]:
        """Execute query safely."""
        if not self.conn:
            return []
        try:
            result = self.conn.execute(query, parameters=params or {})
            columns = result.get_column_names()
            rows = []
            while result.has_next():
                row = result.get_next()
                rows.append(dict(zip(columns, row)))
            return rows
        except Exception as e:
            logger.error("Graph query failed: %s", e)
            return []

    def get_nodes(self, node_type: str = None) -> list[dict]:
        """Get all nodes or filtered by type."""
        if node_type:
            query = f"MATCH (n:{node_type}) RETURN n.* LIMIT {config.TOPOLOGY_QUERY_LIMIT}"
        else:
            query = f"MATCH (n) RETURN n.* LIMIT {config.TOPOLOGY_QUERY_LIMIT}"
        return self._execute(query)

    def get_edges(self) -> list[dict]:
        """Get all edges."""
        query = f"""MATCH (a)-[r]->(b) 
        RETURN a.id as source, b.id as target, type(r) as type, r.* 
        LIMIT {config.TOPOLOGY_EDGES_LIMIT}"""
        return self._execute(query)

    def get_entity(self, entity_id: str) -> dict | None:
        """Get a specific entity."""
        query = "MATCH (n) WHERE n.id = $id RETURN n.*"
        results = self._execute(query, {"id": entity_id})
        return results[0] if results else None

    def get_neighbors(self, entity_id: str) -> list[dict]:
        """Get neighbors of an entity."""
        query = f"""MATCH (n)-[r]-(m) WHERE n.id = $id 
        RETURN m.id, m.name, type(r) as rel_type LIMIT {config.TOPOLOGY_NEIGHBORS_LIMIT}"""
        return self._execute(query, {"id": entity_id})

    def get_blast_radius(self, entity_id: str) -> dict:
        """Calculate blast radius using BFS."""
        query = f"""MATCH (n)-[*1..3]-(m) WHERE n.id = $id 
        RETURN DISTINCT m.id, m.name, m.type LIMIT {config.TOPOLOGY_BLAST_RADIUS_LIMIT}"""
        affected = self._execute(query, {"id": entity_id})
        return {
            "root_cause": entity_id,
            "impacted_entities": affected,
            "impacted_count": len(affected),
        }

    def get_topology_stats(self) -> dict:
        """Get topology statistics."""
        nodes = self._execute("MATCH (n) RETURN count(n) as cnt")
        edges = self._execute("MATCH ()-[r]->() RETURN count(r) as cnt")
        return {
            "total_nodes": nodes[0]["cnt"] if nodes else 0,
            "total_edges": edges[0]["cnt"] if edges else 0,
        }