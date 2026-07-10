# Federation — Layer 12 (Enterprise)

Multi-region federation for OmniWatch 2.0. Enables topology synchronization and region management across distributed deployments.

## Components

### RegionManager (`region_manager.py`)
Manages multiple OmniWatch regions — registration, health monitoring, and querying.

- **Inputs:** Region registration requests, health check responses
- **Outputs:** Region status updates, healthy region lists
- **Storage:** ClickHouse (region state), Redis (health cache)

### TopologySync (`topology_sync.py`)
Synchronizes topology graphs across regions with CRDT-like eventual consistency.

- **Inputs:** Local and remote topology graphs (nodes + edges with versions)
- **Outputs:** Merged graph, conflict list, sync result
- **Model:** Last-write-wins with integer version numbers (vector clocks simplified)

## Sync Model

### Eventual Consistency
- Each region maintains its own topology graph
- Regions periodically sync with each other
- Conflicts are detected and flagged for human resolution

### Conflict Resolution
| Scenario | Resolution |
|----------|------------|
| Different nodes (no overlap) | Merge both |
| Same node, different version | Higher version wins |
| Same node, same version, different data | Conflict detected, flagged |

### Data Structures

**Node:**
```json
{
  "id": "entity-id",
  "name": "display-name",
  "version": 3,
  "updated_at": "2026-07-10T08:00:00Z"
}
```

**Edge:**
```json
{
  "source": "entity-id-1",
  "target": "entity-id-2"
}
```

## Usage

```python
from federation.topology_sync import TopologySync

sync = TopologySync()

# Merge two graphs
merged = sync.merge_graphs(local_graph, remote_graph)

# Detect conflicts before merging
conflicts = sync.detect_conflicts(local_graph, remote_graph)

# Full sync operation
result = sync.sync_topology("region-east", "region-west", local_graph, remote_graph)
```

## Testing

```bash
python -m pytest tests/federation/ -v
```
