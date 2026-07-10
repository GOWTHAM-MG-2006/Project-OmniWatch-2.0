"""
OmniWatch 2.0 — TopoBrain
Component: Blast Radius Calculator
Layer: 5
Phase: 1
Purpose: Computes impacted entities and estimated affected users from a root cause
Inputs: Root cause entity, graph topology
Outputs: Blast radius report with impacted chain and user estimates
"""

import os
import json
import logging
from typing import Any
from datetime import datetime

from topology.graph_database import TopoBrainGraph

logger = logging.getLogger(__name__)


class BlastRadiusCalculator:
    """Computes blast radius of an incident from a root cause entity."""

    def __init__(self, graph: TopoBrainGraph | None = None):
        self.graph = graph or TopoBrainGraph()

    def calculate(self, entity_id: str, max_depth: int = 5) -> dict[str, Any]:
        """Calculate the blast radius starting from an entity.

        Traverses upstream dependencies to find all impacted entities.
        """
        impacted = set()
        visited = set()
        chain = []

        self._traverse_upstream(entity_id, impacted, visited, chain, depth=0, max_depth=max_depth)

        # Remove the root cause itself from impacted
        impacted.discard(entity_id)

        return {
            "root_cause": entity_id,
            "impacted_entities": list(impacted),
            "impacted_count": len(impacted),
            "impact_chain": chain,
            "estimated_users_affected": self._estimate_users(impacted),
            "calculated_at": datetime.utcnow().isoformat(),
        }

    def get_impacted_chain(self, entity_id: str, max_depth: int = 5) -> list[dict[str, Any]]:
        """Get the impact chain (ordered list of affected entities)."""
        result = self.calculate(entity_id, max_depth)
        return result["impact_chain"]

    def estimate_users_affected(self, entity_id: str) -> int:
        """Estimate the number of users affected by an entity failure."""
        result = self.calculate(entity_id)
        return result["estimated_users_affected"]

    def _traverse_upstream(
        self,
        entity_id: str,
        impacted: set,
        visited: set,
        chain: list,
        depth: int,
        max_depth: int,
    ):
        """Recursively traverse upstream dependencies."""
        if depth > max_depth or entity_id in visited:
            return

        visited.add(entity_id)
        impacted.add(entity_id)

        # Get dependents (entities that call/depend on this entity)
        dependents = self.graph.get_dependents(entity_id)
        for dep in dependents:
            dep_id = dep.get("id", "")
            if dep_id and dep_id not in visited:
                chain.append({
                    "step": len(chain) + 1,
                    "entity_id": dep_id,
                    "entity_type": dep.get("type", "unknown"),
                    "relationship": "depends_on",
                    "depth": depth + 1,
                })
                self._traverse_upstream(dep_id, impacted, visited, chain, depth + 1, max_depth)

    def _estimate_users(self, impacted_entities: set) -> int:
        """Estimate affected users based on impacted entities."""
        # Simple heuristic: services with high criticality affect more users
        total_users = 0
        for entity_id in impacted_entities:
            entity = self.graph.get_entity("Service", entity_id)
            if entity:
                criticality = entity.get("criticality", "medium")
                if criticality == "critical":
                    total_users += 10000
                elif criticality == "high":
                    total_users += 5000
                elif criticality == "medium":
                    total_users += 1000
                else:
                    total_users += 100
        return total_users
