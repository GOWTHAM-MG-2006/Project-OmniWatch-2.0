"""
OmniWatch 2.0 — Federation
Component: Topology Sync
Layer: Enterprise (Phase 6)
Purpose: Synchronizes topology graphs across regions with CRDT-like eventual consistency
Inputs: Local and remote topology graphs (nodes + edges with vector clocks/versions)
Outputs: Merged graph, conflict list, sync result
"""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class TopologySync:
    """CRDT-like topology graph synchronization across regions.

    Uses last-write-wins with version numbers (vector clocks simplified to
    integer versions per entity). Identical versions with different data
    constitute a conflict that must be flagged.
    """

    def merge_graphs(self, local: dict, remote: dict) -> dict:
        """Merge two topology graphs using last-write-wins version comparison.

        Args:
            local: Local graph with 'nodes' and 'edges' lists.
            remote: Remote graph with 'nodes' and 'edges' lists.

        Returns:
            Merged graph dict with combined nodes and edges.
        """
        nodes_by_id: dict[str, dict] = {}

        for node in local.get("nodes", []):
            nodes_by_id[node["id"]] = node

        for node in remote.get("nodes", []):
            existing = nodes_by_id.get(node["id"])
            if existing is None:
                nodes_by_id[node["id"]] = node
            elif node["version"] > existing["version"]:
                nodes_by_id[node["id"]] = node

        edges: list[dict] = []
        seen_edges: set[tuple] = set()
        for edge in local.get("edges", []):
            key = (edge["source"], edge["target"])
            if key not in seen_edges:
                edges.append(edge)
                seen_edges.add(key)
        for edge in remote.get("edges", []):
            key = (edge["source"], edge["target"])
            if key not in seen_edges:
                edges.append(edge)
                seen_edges.add(key)

        return {"nodes": list(nodes_by_id.values()), "edges": edges}

    def detect_conflicts(self, local: dict, remote: dict) -> list[dict]:
        """Detect entities modified in both regions at the same version.

        Same version number with different data indicates a simultaneous
        modification that cannot be auto-resolved.

        Args:
            local: Local graph with 'nodes' list.
            remote: Remote graph with 'nodes' list.

        Returns:
            List of conflict dicts with entity_id, local_version, remote_version,
            local_data, and remote_data.
        """
        remote_nodes = {n["id"]: n for n in remote.get("nodes", [])}
        conflicts: list[dict] = []

        for local_node in local.get("nodes", []):
            remote_node = remote_nodes.get(local_node["id"])
            if remote_node is None:
                continue
            if local_node["version"] == remote_node["version"] and local_node != remote_node:
                conflicts.append({
                    "entity_id": local_node["id"],
                    "local_version": local_node["version"],
                    "remote_version": remote_node["version"],
                    "local_data": local_node,
                    "remote_data": remote_node,
                })

        return conflicts

    def sync_topology(
        self,
        local_region: str,
        remote_region: str,
        local_graph: dict,
        remote_graph: dict,
    ) -> dict:
        """Perform full topology sync between two regions.

        Merges graphs, detects conflicts, and returns a summary result.

        Args:
            local_region: Name/ID of the local region.
            remote_region: Name/ID of the remote region.
            local_graph: Local topology graph.
            remote_graph: Remote topology graph.

        Returns:
            Dict with merged graph, counts, conflicts, and status.
        """
        merged = self.merge_graphs(local_graph, remote_graph)
        conflicts = self.detect_conflicts(local_graph, remote_graph)

        result = {
            "local_region": local_region,
            "remote_region": remote_region,
            "nodes_merged": len(merged["nodes"]),
            "edges_merged": len(merged["edges"]),
            "conflicts": len(conflicts),
            "conflict_details": conflicts,
            "merged_graph": merged,
            "status": "success",
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

        if conflicts:
            result["status"] = "conflicts_detected"
            logger.warning(
                "Topology sync between %s and %s detected %d conflicts",
                local_region,
                remote_region,
                len(conflicts),
            )

        logger.info(
            "Topology sync %s → %s: %d nodes, %d edges, %d conflicts",
            local_region,
            remote_region,
            result["nodes_merged"],
            result["edges_merged"],
            result["conflicts"],
        )

        return result
