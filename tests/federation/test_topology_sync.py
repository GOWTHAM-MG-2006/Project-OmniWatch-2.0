"""
OmniWatch 2.0 — Federation
Component: Topology Sync Tests
Layer: Enterprise (Phase 6)
Purpose: Unit tests for CRDT-like topology graph merging and conflict detection
"""

from federation.topology_sync import TopologySync


class TestTopologySync:
    """Test cases for TopologySync class."""

    def test_merge_graphs_no_conflicts(self):
        """Two different nodes merge to 2 nodes, no conflicts."""
        sync = TopologySync()
        local = {
            "nodes": [{"id": "A", "name": "frontend", "version": 1, "updated_at": "2026-07-10T08:00:00Z"}],
            "edges": [{"source": "A", "target": "B"}],
        }
        remote = {
            "nodes": [{"id": "C", "name": "database", "version": 1, "updated_at": "2026-07-10T08:00:00Z"}],
            "edges": [{"source": "C", "target": "D"}],
        }
        result = sync.merge_graphs(local, remote)
        assert len(result["nodes"]) == 2
        node_ids = {n["id"] for n in result["nodes"]}
        assert node_ids == {"A", "C"}

    def test_merge_graphs_with_conflict(self):
        """Same node, higher version wins."""
        sync = TopologySync()
        local = {
            "nodes": [{"id": "A", "name": "frontend", "version": 1, "updated_at": "2026-07-10T08:00:00Z"}],
            "edges": [],
        }
        remote = {
            "nodes": [{"id": "A", "name": "frontend-v2", "version": 3, "updated_at": "2026-07-10T08:01:00Z"}],
            "edges": [],
        }
        result = sync.merge_graphs(local, remote)
        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["version"] == 3
        assert result["nodes"][0]["name"] == "frontend-v2"

    def test_detect_conflicts(self):
        """Detects simultaneous modifications (same version, different data)."""
        sync = TopologySync()
        local = {
            "nodes": [{"id": "A", "name": "frontend", "version": 2, "updated_at": "2026-07-10T08:00:00Z"}],
            "edges": [],
        }
        remote = {
            "nodes": [{"id": "A", "name": "frontend-remote", "version": 2, "updated_at": "2026-07-10T08:00:30Z"}],
            "edges": [],
        }
        conflicts = sync.detect_conflicts(local, remote)
        assert len(conflicts) == 1
        assert conflicts[0]["entity_id"] == "A"
        assert conflicts[0]["local_version"] == 2
        assert conflicts[0]["remote_version"] == 2

    def test_sync_topology(self):
        """Full sync returns merged counts."""
        sync = TopologySync()
        local = {
            "nodes": [{"id": "A", "name": "frontend", "version": 1, "updated_at": "2026-07-10T08:00:00Z"}],
            "edges": [{"source": "A", "target": "B"}],
        }
        remote = {
            "nodes": [{"id": "C", "name": "database", "version": 1, "updated_at": "2026-07-10T08:00:00Z"}],
            "edges": [{"source": "C", "target": "D"}],
        }
        result = sync.sync_topology("region-east", "region-west", local, remote)
        assert result["nodes_merged"] == 2
        assert result["edges_merged"] == 2
        assert result["conflicts"] == 0
        assert result["status"] == "success"
