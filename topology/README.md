# Topology Layer (Layer 5: TopoBrain)

## Causal Knowledge Graph

8-layer entity model with <500ms update latency for real-time topology awareness.

### 8-Layer Entity Model

| Layer | Entity Types | Description |
|-------|-------------|-------------|
| 1 | Service | Microservices, APIs, endpoints |
| 2 | Process | Containers, pods, processes |
| 3 | Host | VMs, bare metal, cloud instances |
| 4 | Infrastructure | Load balancers, networks, storage |
| 5 | Database | PostgreSQL, MongoDB, Redis, etc. |
| 6 | GenAI Service | LLM endpoints, embedding services |
| 7 | Business Transaction | Revenue-critical user flows |
| 8 | Cost Center | Cost allocation, carbon tracking |

## Components

- **graph_database.py** — TopoBrain graph operations using Apache Kuzu
- **topology_processor.py** — Processes topology deltas from Kafka (Flink)
- **entity_registry.py** — Redis cache + ClickHouse entity history
- **drift_detector.py** — Runtime vs declared architecture comparison
- **blast_radius_calculator.py** — Computes impacted entities (graph traversal)

## Node Types (Kuzu Labels)

| Label | Key Properties |
|-------|---------------|
| `:Service` | id, name, type, criticality, cloud_provider, anomaly_score |
| `:Process` | id, name, container_id, pod_id, host_id, anomaly_score |
| `:Host` | id, name, type, cloud_provider, region, cpu, memory |
| `:Infrastructure` | id, name, type, cloud_provider, status |
| `:Database` | id, name, type, cloud_provider, status |
| `:GenAIService` | id, name, model, provider, token_cost, latency |
| `:BusinessTransaction` | id, name, revenue_impact, sla_target, error_budget |
| `:CostCenter` | id, name, hourly_cost_usd, carbon_grams_per_hour |

## Relationship Types

| Relationship | Properties |
|-------------|-----------|
| `:CALLS` | latency_p50, latency_p95, latency_p99, error_rate |
| `:READS_FROM` | query_type, avg_duration_ms |
| `:DEPENDS_ON` | dependency_type, criticality |
| `:DEPLOYED_ON` | deployment_version, deployed_at |
| `:HOSTED_BY` | cost_center_id, hourly_cost |
| `:INFERRED_BY` | causal_score, confidence, method |

## Data Flow

```
StreamForge → omniwatch.topology.deltas (Kafka) → TopoBrain
    → Kuzu graph updates (<500ms latency)
    → Entity registry (Redis cache + ClickHouse history)
    → Drift detection (runtime vs declared)
    → Blast radius calculation (graph traversal)
```

## Technology

- Apache Kuzu (embedded graph database, <500ms updates)
- Redis (entity cache, deduplication)
- Apache Flink (stream processing)
- ClickHouse (entity history)
