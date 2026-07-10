# OmniWatch 2.0 — Phase 1: Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete Phase 1 foundation — directory structure, infrastructure stack, storage layer (Layer 4), stream processing (Layer 3), topology graph (Layer 5), dashboard (Layer 11), and testing services.

**Architecture:** 11-layer AIOps platform with eBPF collection, Kafka/Flink streaming, ClickHouse/Kuzu/MinIO storage, FastAPI backend, and React 19 frontend. Phase 1 focuses on data ingestion pipeline, storage foundation, basic topology, and dashboard UI.

**Tech Stack:** Python 3.11+, React 19, TypeScript, Vite, TailwindCSS, FastAPI, Apache Kafka, ClickHouse, Apache Kuzu, MinIO, Redis, OPA, Ollama, Docker

---

## Global Constraints

- Python 3.11+ only
- Every Python file requires the OmniWatch 2.0 header block
- Naming: snake_case (files/functions), PascalCase (classes)
- All services must have Dockerfile, README.md, .env, JSON logging, /health endpoint
- Git commits: `phase1: <component> — <description>`
- No real AWS/Azure/GCP credentials — mock/simulate only
- No simulation/ directory — telemetry from external system
- Technologies: ONLY those listed in AGENTS.md tech stack

---

## Task 1: Directory Structure & READMEs

**Covers:** Repository scaffolding

**Files:**
- Create: All directories per AGENTS.md Repository Structure
- Create: `ingestion/README.md`, `storage/README.md`, `topology/README.md`, `ai/README.md`, `remediation/README.md`, `simulation_engine/README.md`, `security/README.md`, `learning/README.md`, `dashboard/README.md`

- [ ] **Step 1: Create full directory tree**

```powershell
$dirs = @(
    "ingestion/ghost_collector/probes",
    "ingestion/ghost_collector/controller",
    "ingestion/ghost_collector/otel_receiver",
    "ingestion/ghost_collector/cloud_api_poller",
    "ingestion/ghost_collector/rum_agent",
    "ingestion/ghost_collector/llm_observer",
    "ingestion/ghost_collector/edge_processor",
    "ingestion/ghost_collector/watchdog",
    "ingestion/stream_forge",
    "storage/cold_store",
    "storage/nql_engine",
    "topology",
    "ai/causal",
    "ai/predictive",
    "ai/generative",
    "ai/diff_engine",
    "remediation/auto_heal",
    "remediation/config_drift",
    "remediation/policies",
    "simulation_engine",
    "security",
    "learning",
    "dashboard/backend/routes",
    "dashboard/frontend/src/pages",
    "dashboard/frontend/src/components",
    "dashboard/frontend/src/hooks",
    "k8s/simulated-services",
    "k8s/omniwatch",
    "k8s/argocd",
    ".github/workflows"
)
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}
```

- [ ] **Step 2: Create placeholder README.md files for each layer directory**

Each README should contain the layer name, purpose, and list of components.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "phase1: scaffolding — create full directory structure and READMEs"
```

---

## Task 2: Infrastructure Stack (docker-compose.yml + .env.example)

**Covers:** Docker infrastructure for all Phase 1 services

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: Create docker-compose.yml**

Services:
- `zookeeper` (confluentinc/cp-zookeeper:7.6.0)
- `kafka` (confluentinc/cp-kafka:7.6.0) — port 9092
- `clickhouse` (clickhouse/clickhouse-server:24.3) — port 9000 (native), 8123 (HTTP)
- `minio` (minio/minio:latest) — port 9000 (API), 9001 (console), minioadmin/minioadmin
- `redis` (redis:7-alpine) — port 6379
- `opa` (openpolicyagent/opa:latest) — port 8181
- `ollama` (ollama/ollama:latest) — port 11434
- `dashboard-backend` (build from dashboard/backend/) — port 8000
- `dashboard-frontend` (build from dashboard/frontend/) — port 3000

Kafka should have health check. MinIO needs `server /data --console-address :9001`. ClickHouse no password.

- [ ] **Step 2: Create .env.example**

All environment variables referenced in docker-compose and application configs.

- [ ] **Step 3: Validate docker-compose syntax**

```powershell
docker-compose config
```

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml .env.example
git commit -m "phase1: infrastructure — add docker-compose with Kafka, ClickHouse, MinIO, Redis, OPA, Ollama"
```

---

## Task 3: Layer 4 — ClickHouse Schema (schema.sql)

**Covers:** All ClickHouse table definitions for warm storage tier

**Files:**
- Create: `storage/schema.sql`

- [ ] **Step 1: Create schema.sql**

11 tables matching AGENTS.md Storage Reference:
- `metrics` — time-series metrics (MergeTree, partition by toYYYYMM(timestamp))
- `logs` — log events (MergeTree, partition by toYYYYMM(timestamp))
- `traces` — distributed spans (MergeTree)
- `anomalies` — anomaly records (MergeTree)
- `incidents` — incident records (ReplacingMergeTree)
- `profiles` — profiling data (MergeTree)
- `pending_approvals` — approval queue (ReplacingMergeTree)
- `knowledge_base` — resolved incidents (ReplacingMergeTree)
- `simulations` — simulation results (ReplacingMergeTree)
- `config_drifts` — drift events (MergeTree)
- `cost_carbon` — cost/carbon data (MergeTree)

Each table must use the `omniwatch` database, have appropriate ORDER BY, and match the query patterns from AGENTS.md.

- [ ] **Step 2: Commit**

```bash
git add storage/schema.sql
git commit -m "phase1: nexusstore — add ClickHouse schema for all 11 tables"
```

---

## Task 4: Layer 4 — Storage Clients (Python)

**Covers:** Hot store, warm store, graph store, object store, bucket setup

**Files:**
- Create: `storage/hot_store.py`
- Create: `storage/warm_store.py`
- Create: `storage/graph_store.py`
- Create: `storage/object_store.py`
- Create: `storage/bucket_setup.py`

- [ ] **Step 1: Create hot_store.py** — Apache Arrow in-memory columnar store interface

Class `HotStore` with methods: `ingest_batch()`, `query()`, `flush_to_warm()`. Uses `pyarrow`.

- [ ] **Step 2: Create warm_store.py** — ClickHouse client

Class `WarmStore` with methods: `insert_metrics()`, `insert_logs()`, `insert_traces()`, `query_metrics()`, `query_logs()`. Uses `clickhouse_connect`.

- [ ] **Step 3: Create graph_store.py** — Apache Kuzu graph client

Class `GraphStore` with methods: `create_node()`, `create_relationship()`, `query_neighbors()`, `shortest_path()`, `get_subgraph()`. Uses `kuzu` embedded database. Must handle all 8 node types and 6 relationship types from AGENTS.md.

- [ ] **Step 4: Create object_store.py** — MinIO/S3 client

Class `ObjectStore` with methods: `upload()`, `download()`, `list_objects()`, `delete()`. Uses `minio` Python client.

- [ ] **Step 5: Create bucket_setup.py** — Creates all 7 MinIO buckets

Script that creates the 7 buckets from AGENTS.md MinIO Buckets reference.

- [ ] **Step 6: Verify Python imports**

```powershell
python -c "from storage.hot_store import HotStore; from storage.warm_store import WarmStore; from storage.graph_store import GraphStore; from storage.object_store import ObjectStore; print('All imports OK')"
```

- [ ] **Step 7: Commit**

```bash
git add storage/hot_store.py storage/warm_store.py storage/graph_store.py storage/object_store.py storage/bucket_setup.py
git commit -m "phase1: nexusstore — implement Arrow hot store, ClickHouse warm store, Kuzu graph store, MinIO object store"
```

---

## Task 5: Layer 3 — StreamForge Kafka Bus & Entity Resolution

**Covers:** Kafka producer/consumer classes, entity resolution with Redis

**Files:**
- Create: `ingestion/stream_forge/kafka_bus.py`
- Create: `ingestion/stream_forge/entity_resolution.py`

- [ ] **Step 1: Create kafka_bus.py**

Classes: `KafkaProducer`, `KafkaConsumer`. Uses `confluent-kafka`. Support all 11 topics from AGENTS.md Kafka Topics Reference. Methods: `produce(topic, key, value)`, `consume(topic, group_id, callback)`.

- [ ] **Step 2: Create entity_resolution.py**

Class `EntityResolution` using Redis cache. Methods: `resolve_entity(volatile_id, entity_type)`, `get_stable_id(volatile_id)`, `register_mapping(volatile_id, stable_id)`. Maps pod UIDs, container IDs, IPs to stable entity IDs.

- [ ] **Step 3: Commit**

```bash
git add ingestion/stream_forge/kafka_bus.py ingestion/stream_forge/entity_resolution.py
git commit -m "phase1: streamforge — add Kafka bus classes and Redis-backed entity resolution"
```

---

## Task 6: Layer 3 — StreamForge Processing Pipeline

**Covers:** Windowing, enrichment, validation, PII, sampling, topology publishing

**Files:**
- Create: `ingestion/stream_forge/windowing_layer.py`
- Create: `ingestion/stream_forge/enrichment_engine.py`
- Create: `ingestion/stream_forge/receipt_validation.py`
- Create: `ingestion/stream_forge/pii_engine.py`
- Create: `ingestion/stream_forge/adaptive_intelligence.py`
- Create: `ingestion/stream_forge/topology_publisher.py`

- [ ] **Step 1: Create windowing_layer.py**

Class `WindowingLayer` — Flink-compatible tumbling windows + feature engineering. Methods: `create_windows()`, `compute_features()`, `emit_windowed_vectors()`. Produces ML-ready feature vectors.

- [ ] **Step 2: Create enrichment_engine.py**

Class `EnrichmentEngine` — semantic normalization. Methods: `enrich(raw_telemetry)`, `normalize_entity()`, `add_topology_context()`.

- [ ] **Step 3: Create receipt_validation.py**

Class `ReceiptValidation` — multi-protocol ingest validation. Methods: `validate_metric()`, `validate_log()`, `validate_trace()`. Checks schema compliance.

- [ ] **Step 4: Create pii_engine.py**

Class `PIIEngine` — PII detection stub using Presidio. Methods: `detect_pii(text)`, `anonymize(text, entities)`.

- [ ] **Step 5: Create adaptive_intelligence.py**

Class `AdaptiveIntelligence` — tail-based sampling. Methods: `should_sample(telemetry, anomaly_score)`, `route_anomaly()`.

- [ ] **Step 6: Create topology_publisher.py**

Class `TopologyPublisher` — publishes topology deltas to Kafka. Methods: `publish_delta(entity, change_type)`, `emit_to_topic()`.

- [ ] **Step 7: Commit**

```bash
git add ingestion/stream_forge/windowing_layer.py ingestion/stream_forge/enrichment_engine.py ingestion/stream_forge/receipt_validation.py ingestion/stream_forge/pii_engine.py ingestion/stream_forge/adaptive_intelligence.py ingestion/stream_forge/topology_publisher.py
git commit -m "phase1: streamforge — add windowing, enrichment, validation, PII, sampling, topology publisher"
```

---

## Task 7: Layer 5 — TopoBrain Graph Operations

**Covers:** Graph database operations, topology processing, entity registry, drift detection, blast radius

**Files:**
- Create: `topology/graph_database.py`
- Create: `topology/topology_processor.py`
- Create: `topology/entity_registry.py`
- Create: `topology/drift_detector.py`
- Create: `topology/blast_radius_calculator.py`

- [ ] **Step 1: Create graph_database.py**

Class `TopoBrainGraph` using Kuzu. Full CRUD for all 8 node types and 6 relationship types. Methods: `add_service()`, `add_host()`, `add_database()`, `add_relationship()`, `get_dependencies()`, `update_anomaly_score()`.

- [ ] **Step 2: Create topology_processor.py**

Class `TopologyProcessor` — processes topology deltas from Kafka. Methods: `process_delta(delta)`, `apply_to_graph()`, `emit_updates()`.

- [ ] **Step 3: Create entity_registry.py**

Class `EntityRegistry` — Redis cache + ClickHouse history. Methods: `register_entity()`, `get_entity()`, `update_status()`, `get_history()`.

- [ ] **Step 4: Create drift_detector.py**

Class `DriftDetector` — runtime vs declared architecture. Methods: `compare(runtime_graph, declared_config)`, `detect_drift()`, `report_drift()`.

- [ ] **Step 5: Create blast_radius_calculator.py**

Class `BlastRadiusCalculator` — computes impacted entities. Methods: `calculate(entity_id)`, `get_impacted_chain()`, `estimate_users_affected()`.

- [ ] **Step 6: Commit**

```bash
git add topology/graph_database.py topology/topology_processor.py topology/entity_registry.py topology/drift_detector.py topology/blast_radius_calculator.py
git commit -m "phase1: to pobrai n — implement graph operations, topology processor, entity registry, drift detector, blast radius calculator"
```

---

## Task 8: Layer 11 — FastAPI Backend

**Covers:** API gateway, all route files, WebSocket, Dockerfile

**Files:**
- Create: `dashboard/backend/main.py`
- Create: `dashboard/backend/routes/incidents.py`
- Create: `dashboard/backend/routes/topology.py`
- Create: `dashboard/backend/routes/metrics.py`
- Create: `dashboard/backend/routes/approvals.py`
- Create: `dashboard/backend/routes/knowledge.py`
- Create: `dashboard/backend/routes/simulations.py`
- Create: `dashboard/backend/routes/security.py`
- Create: `dashboard/backend/routes/config_drift.py`
- Create: `dashboard/backend/routes/reports.py`
- Create: `dashboard/backend/websocket.py`
- Create: `dashboard/backend/Dockerfile`

- [ ] **Step 1: Create main.py** — FastAPI app with /health, CORS, include all routers

- [ ] **Step 2: Create all 9 route files** — Each with stub CRUD endpoints matching their domain

- [ ] **Step 3: Create websocket.py** — WebSocket endpoint for real-time event streaming

- [ ] **Step 4: Create Dockerfile** — Python 3.11-slim, install deps, run uvicorn

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/
git commit -m "phase1: nexusux — add FastAPI backend with all route stubs, WebSocket, Dockerfile"
```

---

## Task 9: Layer 11 — React Frontend

**Covers:** Vite + React 19 + TypeScript + TailwindCSS setup, App.tsx with routing

**Files:**
- Create: `dashboard/frontend/package.json`
- Create: `dashboard/frontend/vite.config.ts`
- Create: `dashboard/frontend/tsconfig.json`
- Create: `dashboard/frontend/index.html`
- Create: `dashboard/frontend/tailwind.config.js` (if v3) or CSS import (v4)
- Create: `dashboard/frontend/src/App.tsx`
- Create: `dashboard/frontend/src/main.tsx`
- Create: `dashboard/frontend/src/index.css`
- Create: `dashboard/frontend/Dockerfile`

- [ ] **Step 1: Create package.json** — React 19, TypeScript 5.x, Vite 6.x, TailwindCSS 4.x, react-router-dom, sigma.js, graphology, recharts, d3.js

- [ ] **Step 2: Create vite.config.ts** — Vite config with React plugin, proxy to backend :8000

- [ ] **Step 3: Create App.tsx** — React Router with all 11 page routes (SREMode, DeveloperMode, ExecutiveMode, SecurityMode, IncidentExplorer, TopologyViewer, KnowledgeBase, PolicyManager, SimulaXDashboard, ConfigDriftView, AIFirstChat)

- [ ] **Step 4: Create main.tsx, index.css** — React entry point with TailwindCSS import

- [ ] **Step 5: Create Dockerfile** — Node 20, build, serve with nginx

- [ ] **Step 6: Verify build**

```powershell
cd dashboard/frontend; npm install; npm run build
```

- [ ] **Step 7: Commit**

```bash
git add dashboard/frontend/
git commit -m "phase1: nexusux — add React 19 frontend with routing, Vite config, Dockerfile"
```

---

## Task 10: Testing Services & K8s Manifests

**Covers:** Fake microservices for testing, basic K8s manifests

**Files:**
- Create: `k8s/simulated-services/payment-service/app.py`
- Create: `k8s/simulated-services/payment-service/Dockerfile`
- Create: `k8s/simulated-services/inventory-service/app.py`
- Create: `k8s/simulated-services/inventory-service/Dockerfile`
- Create: `k8s/simulated-services/docker-compose.yml`

- [ ] **Step 1: Create payment-service** — FastAPI app that simulates a payment microservice with /health, /pay, /refund endpoints, emits mock telemetry

- [ ] **Step 2: Create inventory-service** — FastAPI app that simulates inventory with /health, /check-stock, /reserve endpoints

- [ ] **Step 3: Create simulated-services docker-compose** — Runs both services

- [ ] **Step 4: Commit**

```bash
git add k8s/simulated-services/
git commit -m "phase1: testing — add simulated payment and inventory services"
```

---

## Task 11: Final Validation & .gitignore

**Covers:** End-to-end validation, gitignore updates

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Update .gitignore** — Add __pycache__, .venv/, node_modules/, .env, dist/, build/, *.pyc, .mimocode/

- [ ] **Step 2: Run full docker-compose up**

```powershell
docker-compose up -d
```

Wait for all services to be healthy.

- [ ] **Step 3: Verify health endpoints**

```powershell
curl http://localhost:8000/health
curl http://localhost:9001/minio/health/live
```

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "phase1: foundation — final validation and gitignore updates"
```

---

*Plan Version: 1.0 | Created: 2026-07-10 | Phase: 1 Foundation*
