# Topology Layer (Layer 5: TopoBrain)

## Causal Knowledge Graph

8-layer entity model with <500ms update latency:

- Service, Process, Host, Infrastructure, Database, GenAI Service, Business Transaction, Cost Center

## Components

- **graph_database.py** — TopoBrain graph operations using Apache Kuzu
- **topology_processor.py** — Processes topology deltas from Kafka
- **entity_registry.py** — Redis cache + ClickHouse entity history
- **drift_detector.py** — Runtime vs declared architecture comparison
- **blast_radius_calculator.py** — Computes impacted entities

## Node Types

Service, Process, Host, Infrastructure, Database, GenAIService, BusinessTransaction, CostCenter

## Relationship Types

CALLS, READS_FROM, DEPENDS_ON, DEPLOYED_ON, HOSTED_BY, INFERRED_BY

## Data Flow

```
StreamForge → omniwatch.topology.deltas (Kafka) → TopoBrain
    → Kuzu graph updates → Neo4j-compatible queries
    → Drift detection → Blast radius calculation
```

## Technology

- Apache Kuzu (embedded graph database)
- Redis (entity cache, deduplication)
- Apache Flink (stream processing)
