# Storage Layer (Layer 4: NexusStore)

## Unified Data Lakehouse

Four-tier storage architecture optimized for different access patterns and retention requirements.

### Storage Tiers

| Tier | Technology | Purpose | Retention |
|------|-----------|---------|-----------|
| **Hot** | Apache Arrow | In-memory columnar store for real-time queries | < 1 hour |
| **Warm** | ClickHouse | Time-series metrics, logs, traces | 1-90 days |
| **Cold** | Apache Parquet + Iceberg | Aged telemetry, ML training datasets | > 90 days |
| **Graph** | Apache Kuzu | Causal knowledge graph (8-layer topology) | Permanent |
| **Object** | MinIO/S3 | Runbooks, compliance evidence, artifacts | Permanent |

## Components

### Core Storage
- **hot_store.py** — Apache Arrow in-memory columnar store (real-time queries)
- **warm_store.py** — ClickHouse client for warm tier (time-series optimized)
- **object_store.py** — MinIO/S3 object storage client
- **bucket_setup.py** — Creates all required MinIO buckets
- **schema.sql** — All ClickHouse table definitions (11 tables)

### Cold Storage (Phase 2)
- **cold_store/parquet_writer.py** — Efficient Parquet file writer with columnar compression
- **cold_store/iceberg_manager.py** — Apache Iceberg table management (schema evolution, partitioning)
- **cold_store/duckdb_query.py** — DuckDB query engine for fast cold Parquet queries

### NexusQL Engine (Phase 2)
- **nql_engine/parser.py** — NexusQL query parser (SQL-like syntax for cross-signal queries)
- **nql_engine/planner.py** — Query execution planner (cost-based optimization)
- **nql_engine/executor.py** — Cross-signal query executor (unified hot/warm/cold access)

## ClickHouse Tables

| Table | Purpose | Primary Key |
|-------|---------|-------------|
| metrics | Time-series metrics (windowed) | entity_id, timestamp |
| logs | Log events | entity_id, timestamp |
| traces | Distributed spans | trace_id, service |
| anomalies | Detected anomalies | anomaly_id, timestamp |
| incidents | Full incident records | incident_id, created_at |
| profiles | Continuous profiling data | entity_id, timestamp |
| pending_approvals | Awaiting human approval | approval_id, status |
| knowledge_base | Resolved incident outcomes | root_cause_entity_type |
| simulations | SimulaX simulation results | simulation_id, mode |
| config_drifts | Configuration drift events | drift_id, drift_source |
| cost_carbon | Per-entity cost + carbon | entity_id, timestamp |

## MinIO Buckets

| Bucket | Contents |
|--------|----------|
| omniwatch-telemetry-archive | Aged telemetry > 90 days (Parquet) |
| omniwatch-incidents | Full incident JSON records |
| omniwatch-audit-logs | All remediation + drift action logs |
| omniwatch-ml-datasets | Historical data for model training |
| omniwatch-runbooks | Generated runbooks and playbooks |
| omniwatch-compliance | SOC2/ISO27001 evidence packages |
| omniwatch-simulations | SimulaX simulation results archive |

## NexusQL Example

```sql
-- Query across hot/warm/cold tiers
SELECT entity_id, AVG(query_time_p99) as avg_latency
FROM metrics
WHERE entity_id = 'payment-db'
  AND timestamp > NOW() - INTERVAL 30 DAY
GROUP BY entity_id
HAVING avg_latency > 1000;
```

## Technology

- Apache Arrow (hot tier, in-memory columnar)
- ClickHouse (warm tier, time-series optimized)
- Apache Parquet + Iceberg (cold tier, columnar files)
- DuckDB (cold tier query engine)
- Apache Kuzu (graph store)
- MinIO/S3 (object storage)
