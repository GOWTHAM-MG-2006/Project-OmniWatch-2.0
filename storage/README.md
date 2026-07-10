# Storage Layer (Layer 4: NexusStore)

## Unified Data Lakehouse

Four-tier storage architecture:

| Tier | Technology | Purpose |
|------|-----------|---------|
| **Hot** | Apache Arrow | In-memory columnar store for real-time queries |
| **Warm** | ClickHouse | Time-series metrics, logs, traces |
| **Cold** | Apache Parquet + Iceberg | Aged telemetry > 90 days |
| **Graph** | Apache Kuzu | Causal knowledge graph |
| **Object** | MinIO/S3 | Runbooks, ML datasets, compliance evidence |

## Components

- **hot_store.py** — Apache Arrow in-memory columnar store
- **warm_store.py** — ClickHouse client for warm tier
- **cold_store/** — Parquet writer, Iceberg manager, DuckDB query engine
- **graph_store.py** — Apache Kuzu embedded graph client
- **object_store.py** — MinIO/S3 object storage client
- **bucket_setup.py** — Creates all required MinIO buckets
- **schema.sql** — All ClickHouse table definitions
- **nql_engine/** — NexusQL query language (parser, planner, executor)

## ClickHouse Tables

metrics, logs, traces, anomalies, incidents, profiles, pending_approvals, knowledge_base, simulations, config_drifts, cost_carbon

## MinIO Buckets

omniwatch-telemetry-archive, omniwatch-incidents, omniwatch-audit-logs, omniwatch-ml-datasets, omniwatch-runbooks, omniwatch-compliance, omniwatch-simulations
