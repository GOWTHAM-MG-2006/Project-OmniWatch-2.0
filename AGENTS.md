# OmniWatch 2.0 — AGENTS.md

## AI Agent Operational Guide for Codebase Navigation and Development

\---

## Project Identity

|Field|Value|
|-|-|
|**Name**|OmniWatch 2.0|
|**Type**|AI-Driven Cloud Operations (AIOps) Platform|
|**Competition**|IEEE YESIST12 2026 — IEngage Track|
|**Status**|Architecture finalized, starting Phase 1 implementation|
|**Architecture**|11-Layer System + Configuration Drift Engine (Cross-Cutting)|
|**Goal**|Proactive anomaly detection, causal root cause analysis, autonomous remediation, digital twin simulation, and self-healing for cloud-native environments|

\---

## Repository Structure

```
Project-OmniWatch-2.0/
├── AGENTS.md                          ← You are here
├── README.md                          ← Project overview
├── docker-compose.yml                 ← Full local infrastructure stack
├── .env.example                       ← Environment variable template
│
├── docs/                              ← Architecture \& Design Documents
│   ├── New-System-Architecture.md     ← 11-layer architecture spec
│   ├── DataFlow.md                    ← End-to-end data flow
│   ├── DSL-Documentation-Code.txt     ← Structurizr DSL model
│   ├── Simple-New-System-DataFlow.md  ← ASCII architecture overview
│   ├── Build-Plan.md                  ← 4-phase, 24-month roadmap
│   ├── Competitor-Analysis.md         ← Dynatrace deep-dive
│   ├── Open-Source-Comparison.md      ← OSS vs Dynatrace
│   ├── Enterprise-Comparison.md       ← Enterprise vs Dynatrace
│   └── Master-Comparison.md           ← Three-way comparison
│
├── ingestion/                         ← LAYER 2+3: Collection + Stream Processing
│   ├── ghost\_collector/               ← eBPF collection engine
│   │   ├── probes/                    ← eBPF C programs (kprobes, uprobes, LSM)
│   │   ├── controller/                ← Rust user-space controller
│   │   ├── otel\_receiver/             ← OTLP receiver (gRPC + HTTP)
│   │   ├── cloud\_api\_poller/          ← AWS/Azure/GCP API polling
│   │   ├── rum\_agent/                 ← Browser/mobile RUM (JS injection)
│   │   ├── llm\_observer/              ← LLM/GenAI workload observability
│   │   ├── edge\_processor/            ← In-agent edge computing (eBPF maps)
│   │   └── watchdog/                  ← Self-healing health monitor
│   ├── stream\_forge/                  ← Intelligent ingest pipeline
│   │   ├── receipt\_validation.py      ← Multi-protocol ingest + validation
│   │   ├── enrichment\_engine.py       ← Semantic normalization + enrichment
│   │   ├── entity\_resolution.py       ← Volatile ID → stable entity mapping
│   │   ├── windowing\_layer.py         ← Flink windowing + feature engineering
│   │   ├── adaptive\_intelligence.py   ← Tail-based sampling + anomaly routing
│   │   ├── pii\_engine.py              ← Privacy-by-default PII detection (Presidio)
│   │   ├── topology\_publisher.py      ← Publishes deltas to TopoBrain
│   │   └── kafka\_bus.py               ← Kafka producer/consumer classes
│   └── README.md
│
├── storage/                           ← LAYER 4: Unified Data Lakehouse
│   ├── hot\_store.py                   ← Apache Arrow in-memory columnar store
│   ├── warm\_store.py                  ← ClickHouse client (warm tier)
│   ├── cold\_store/
│   │   ├── parquet\_writer.py          ← Parquet file writer
│   │   ├── iceberg\_manager.py         ← Iceberg table management
│   │   └── duckdb\_query.py            ← DuckDB query engine for cold Parquet
│   ├── graph\_store.py                 ← Apache Kuzu graph client (embedded)
│   ├── object\_store.py                ← MinIO/S3 object storage client
│   ├── bucket\_setup.py                ← Creates all required MinIO buckets
│   ├── schema.sql                     ← All ClickHouse table definitions
│   ├── nql\_engine/                    ← NexusQL query language
│   │   ├── parser.py                  ← NQL query parser
│   │   ├── planner.py                 ← Query execution planner
│   │   └── executor.py                ← Cross-signal query executor
│   └── README.md
│
├── topology/                          ← LAYER 5: Causal Knowledge Graph
│   ├── graph\_database.py              ← TopoBrain graph operations (Kuzu)
│   ├── topology\_processor.py          ← Processes topology deltas (Flink)
│   ├── entity\_registry.py             ← Redis cache + ClickHouse history
│   ├── drift\_detector.py              ← Runtime vs declared architecture
│   ├── blast\_radius\_calculator.py     ← Impact computation
│   └── README.md
│
├── ai/                                ← LAYER 6: NeuroEngine (Hypermodal AI)
│   ├── causal/
│   │   ├── baseline\_engine.py         ← Holt-Winters + ARIMA baselines
│   │   ├── anomaly\_detector.py        ← Multi-signal anomaly detection
│   │   ├── causal\_graph\_traversal.py  ← GNN (PyTorch Geometric) + Granger + DAG walker
│   │   ├── problem\_assembler.py       ← Groups anomalies → ONE Problem
│   │   └── root\_cause\_builder.py      ← Packages RootCauseObject
│   ├── predictive/
│   │   ├── prophet\_forecaster.py      ← Seasonality-aware forecasting
│   │   ├── lstm\_forecaster.py         ← Non-linear pattern forecasting (PyTorch)
│   │   └── predictive\_trigger.py      ← Auto-triggers AutoHeal
│   ├── generative/
│   │   ├── grounded\_llm\_client.py     ← Hallucination-safe LLM client (vLLM + LiteLLM)
│   │   ├── output\_validator.py        ← Validates LLM output against input
│   │   ├── incident\_summary.py        ← Generates ops engineer summaries
│   │   ├── executive\_report.py        ← Generates non-technical reports
│   │   ├── runbook\_generator.py       ← Generates step-by-step runbooks
│   │   ├── post\_incident\_analyser.py  ← Post-mortem report generation
│   │   └── dashboard\_generator.py     ← Auto-generates dashboards
│   ├── diff\_engine/                   ← Differential analysis (BubbleUp extended)
│   │   ├── diff\_analyzer.py           ← Cross-signal comparison
│   │   └── causal\_hypothesis.py       ← Ranked causal hypotheses
│   ├── grounding\_guard.py             ← Evidence-backed output validation
│   └── README.md
│
├── remediation/                       ← LAYER 7: AutoHeal + Config Drift
│   ├── auto\_heal/
│   │   ├── policy\_engine.py           ← OPA Rego policy evaluation
│   │   ├── approval\_workflow.py       ← Human-in-the-loop approval
│   │   ├── action\_library.py          ← Predefined remediation actions
│   │   ├── remediation\_engine.py      ← Executes K8s/cloud API actions
│   │   └── rollback\_manager.py        ← Auto-generated rollback plans
│   ├── config\_drift/                  ← Configuration Drift Engine
│   │   ├── drift\_detector.py          ← Detects drift across all layers
│   │   ├── argocd\_integrator.py       ← K8s drift → ArgoCD self-heal
│   │   ├── ansible\_integrator.py      ← OS drift → Ansible EDA playbook
│   │   ├── terraform\_integrator.py    ← Cloud drift → Terraform state
│   │   └── git\_integrator.py          ← Git drift → Auto-revert commit
│   ├── policies/
│   │   ├── remediation.rego           ← OPA: auto vs approval decisions
│   │   ├── security.rego              ← OPA: security action authorization
│   │   └── config\_drift.rego          ← OPA: drift remediation rules
│   └── README.md
│
├── simulation\_engine/                 ← LAYER 8: SimulaX (Digital Twin)
│   ├── digital\_twin.py               ← Continuously updated production model
│   ├── remediation\_sim.py            ← Simulates proposed fixes (SimPy)
│   ├── capacity\_sim.py               ← Simulates traffic growth
│   ├── deployment\_sim.py             ← Simulates deployment rollout
│   ├── chaos\_sim.py                  ← Simulates failure injection
│   ├── bayesian\_calibration.py       ← Auto-tunes model parameters (Optuna)
│   └── README.md
│
├── security/                          ← LAYER 9: SentinelPlane
│   ├── runtime\_security.py           ← eBPF LSM hooks (privilege, escape, RCE)
│   ├── vulnerability\_manager.py      ← SBOM (Syft) + CVE correlation (Grype) + reachability
│   ├── cspm\_checker.py               ← Cloud Security Posture Management (Checkov)
│   ├── perf\_sec\_correlator.py        ← Performance-security correlation
│   └── README.md
│
├── learning/                          ← LAYER 10: Continuous Learning
│   ├── knowledge\_base.py             ← Persistent incident outcome store (ClickHouse + MinIO)
│   ├── feedback\_loop.py              ← Writes resolution outcomes to KB
│   ├── recommendation\_engine.py      ← Surfaces historically successful actions (Scikit-Learn)
│   ├── pattern\_miner.py              ← Mines recurring incident patterns (PyTorch)
│   └── README.md
│
├── dashboard/                         ← LAYER 11: NexusUX
│   ├── backend/
│   │   ├── main.py                    ← FastAPI API gateway
│   │   ├── routes/
│   │   │   ├── incidents.py           ← Incident CRUD endpoints
│   │   │   ├── topology.py            ← TopoBrain graph endpoints
│   │   │   ├── metrics.py             ← Live metrics endpoints
│   │   │   ├── approvals.py           ← Approval workflow endpoints
│   │   │   ├── knowledge.py           ← Knowledge base endpoints
│   │   │   ├── simulations.py         ← SimulaX simulation endpoints
│   │   │   ├── security.py            ← SentinelPlane endpoints
│   │   │   ├── config\_drift.py        ← Config drift status endpoints
│   │   │   └── reports.py             ← Compliance report endpoints
│   │   ├── websocket.py               ← Real-time event streaming
│   │   └── Dockerfile
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   │   ├── AIFirstChat.tsx     ← Natural language → NQL + answers
│   │   │   │   ├── SREMode.tsx         ← Active problems, evidence, topology
│   │   │   │   ├── DeveloperMode.tsx   ← Traces, flame graphs, git blame
│   │   │   │   ├── ExecutiveMode.tsx   ← SLO, revenue, cost, MTTR
│   │   │   │   ├── SecurityMode.tsx    ← CVE, CSPM, MITRE ATT\&CK
│   │   │   │   ├── IncidentExplorer.tsx ← Drill-down incident timeline
│   │   │   │   ├── TopologyViewer.tsx  ← 8-layer dependency graph (Sigma.js)
│   │   │   │   ├── KnowledgeBase.tsx   ← Historical incidents + runbooks
│   │   │   │   ├── PolicyManager.tsx   ← OPA policy management
│   │   │   │   ├── SimulaXDashboard.tsx ← Digital twin simulation UI
│   │   │   │   └── ConfigDriftView.tsx ← Config drift status + remediation
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── App.tsx
│   │   ├── package.json
│   │   └── vite.config.ts
│   └── README.md
│
├── k8s/                               ← Kubernetes manifests
│   ├── simulated-services/            ← Fake microservices for testing
│   ├── omniwatch/                     ← OmniWatch service deployments
│   └── argocd/                        ← ArgoCD application manifests
│
└── .github/
    └── workflows/
        └── ci.yml                     ← CI pipeline
```

\---

## System Architecture Overview (11 Layers)

```
Layer 1:  DATA SOURCES (K8s │ VMs │ Cloud │ Browsers │ LLM APIs │ Databases)
              │
              ▼
Layer 2:  GHOSTCOLLECTOR (eBPF Kernel │ Bytecode │ OTLP │ Cloud API │ RUM │ LLM)
              │
              ▼
Layer 3:  STREAMFORGE (Entity Resolution │ Windowing │ Tail Sampling │ PII)
              │
              ▼
Layer 4:  NEXUSSTORE (Hot: Arrow │ Warm: ClickHouse │ Cold: Parquet │ Graph: Kuzu)
              │
              ▼
Layer 5:  TOPOBRAIN (8-Layer Graph │ <500ms Updates │ Drift Detection)
              │
              ▼
Layer 6:  NEUROENGINE (Causal │ Predictive │ Generative │ DiffEngine)
              │
              ▼
Layer 7:  AUTOHEAL (OPA Policy │ 5 Autonomy Tiers │ Config Drift → ArgoCD/Ansible/Terraform)
              │
              ├──→ Layer 8: SIMULAX (Digital Twin │ Shadow Simulation)
              │
              ├──→ Layer 9: SENTINELPLANE (Runtime Security │ CVE │ CSPM)
              │
              ▼
Layer 10: CONTINUOUS LEARNING (Feedback Loop │ Pattern Mining │ Recommendations)
              │
              ▼
Layer 11: NEXUSUX (AI-First │ SRE │ Developer │ Executive │ Security)
```

\---

## Technology Stack (Definitive Choices)

**No alternatives. These are the only technologies to use.**

|Layer|Technology|Purpose|
|-|-|-|
|**Layer 2 (Collection)**|eBPF (libbpf + CO-RE), Go, Rust, Protocol Buffers|Zero-code kernel-level telemetry|
|**Layer 3 (Ingest)**|Apache Kafka, Apache Flink, Microsoft Presidio|Stream processing, PII detection|
|**Layer 4 (Storage)**|Apache Arrow (Hot), ClickHouse (Warm), Apache Parquet + Iceberg (Cold), Apache Kuzu (Graph), DuckDB (Cold queries), MinIO (Object)|Unified data lakehouse|
|**Layer 5 (Topology)**|Apache Kuzu, Redis, Flink|8-layer causal knowledge graph|
|**Layer 6 (AI)**|PyTorch Geometric (GNN), Prophet, LSTM (PyTorch), Merlion, Scikit-Learn, statsmodels|Hypermodal AI engine|
|**Layer 6 (GenAI)**|vLLM, LiteLLM, Qwen, Llama 3|BYOM LLM inference|
|**Layer 7 (Remediation)**|OPA Rego, Go, Python|Policy-driven autonomous remediation|
|**Layer 8 (Simulation)**|SimPy, Redis, Optuna|Digital twin \& what-if simulation|
|**Layer 9 (Security)**|eBPF LSM hooks, Grype, Syft, Checkov|Runtime security + CVE + CSPM|
|**Layer 10 (Learning)**|Scikit-Learn, PyTorch, ClickHouse, MinIO|Continuous learning pipeline|
|**Layer 11 (UX)**|React 19, TypeScript, Vite, TailwindCSS, Sigma.js + Graphology, Recharts, D3.js, FastAPI|Role-adaptive dashboard|
|**Drift (Cross-Cutting)**|ArgoCD, Ansible EDA, Terraform|Configuration drift remediation|
|**Infrastructure**|Kubernetes, Docker, Helm, ArgoCD (GitOps)|Container orchestration|

### Backend Languages

|Language|Version|Used In|
|-|-|-|
|**Python**|3.11+|Layers 3, 4, 5, 6, 7, 8, 9, 10, 11 (FastAPI backend)|
|**Go**|1.21+|Layer 7 (remediation engine, action library)|
|**Rust**|1.75+|Layer 2 (eBPF controller, edge processor)|

### Python Packages (Definitive)

|Package|Layer|Purpose|
|-|-|-|
|`fastapi`|11|REST API framework|
|`uvicorn`|11|ASGI server|
|`pydantic`|All|Data validation|
|`confluent-kafka`|3|Kafka producer/consumer|
|`apache-flink`|3|Stream processing|
|`presidio`|3|PII detection and anonymization|
|`clickhouse-connect`|4|ClickHouse client|
|`kuzu`|4, 5|Apache Kuzu embedded graph database|
|`minio`|4|S3-compatible object storage client|
|`duckdb`|4|Cold Parquet query engine|
|`redis`|5, 7, 8|Caching, deduplication, simulation state|
|`torch`|6, 10|PyTorch for GNN, LSTM, pattern mining|
|`torch-geometric`|6|Graph Neural Networks (CausalGNN)|
|`prophet`|6|Seasonality-aware time-series forecasting|
|`salesforce-merlion`|6|Multi-model anomaly detection|
|`statsmodels`|6|Granger causality testing|
|`scikit-learn`|6, 10|ML utilities, recommendation engine|
|`vllm`|6|LLM inference server|
|`litellm`|6|Unified LLM API routing (BYOM)|
|`simpy`|8|Discrete event simulation|
|`optuna`|8|Bayesian hyperparameter calibration|
|`opentelemetry-sdk`|2|OTel instrumentation|
|`httpx`|6|Async HTTP for LLM APIs|
|`requests`|7|HTTP client for OPA|
|`jinja2`|10|Compliance report templating|

### Frontend Packages

|Package|Version|Purpose|
|-|-|-|
|**React**|19|UI framework|
|**TypeScript**|5.x|Type safety|
|**Vite**|6.x|Build tool|
|**TailwindCSS**|4.x|Styling|
|**Sigma.js** + **Graphology**|—|WebGL graph visualization (TopoBrain 8-layer)|
|**Recharts**|2.x|Metrics charts|
|**D3.js**|7.x|Custom visualizations|

\---

## Key Data Contracts

### AnomalySignal (from Layer 3 StreamForge)

```json
{
  "entity\_id": "string",
  "entity\_type": "string",
  "entity\_layer": 5,
  "metric\_name": "string",
  "anomaly\_score": 0.96,
  "confidence": 95,
  "timestamp": "2026-07-03T08:14:32Z",
  "deviation\_from\_baseline": "890ms vs baseline 45ms",
  "topology\_context": {
    "depends\_on": \["entity\_id\_1"],
    "depended\_by": \["entity\_id\_2"]
  }
}
```

### RootCauseObject (from Layer 6 NeuroEngine)

```json
{
  "problem\_id": "PRB-20260703-09421",
  "confidence": 0.94,
  "severity": "CRITICAL",
  "root\_cause": {
    "entity": "postgres-payments-primary",
    "entity\_type": "DATABASE",
    "layer": 4,
    "metric": "query\_execution\_time\_p99",
    "deviation": "1,240ms vs baseline 38ms (+3168%)",
    "causal\_score": 0.94
  },
  "evidence\_chain": \[
    {
      "step": 1,
      "observation": "CPU spike on host payments-db-02 preceded DB latency by 2s",
      "timestamp": "2026-07-03T08:12:09Z",
      "signal\_type": "metric",
      "evidence\_id": "NXS-MTR-4421"
    },
    {
      "step": 2,
      "observation": "Granger causality test: host CPU → DB latency causal (p=0.0003)",
      "signal\_type": "analysis",
      "method": "Granger Causality (lag=2s)",
      "confidence": 0.97
    }
  ],
  "blast\_radius": \[
    { "entity": "payment-service-api", "impact": "p99 latency 890ms", "affected\_users": 12400 }
  ],
  "business\_impact": {
    "affected\_users": 12400,
    "estimated\_revenue\_at\_risk\_usd\_per\_hour": 84200,
    "slo\_breach": "checkout-slo: 99.9% SLO breached"
  }
}
```

### IncidentRecord (from Layer 6 Prioritization)

```json
{
  "incident\_id": "INC-2026-07-001",
  "created\_at": "2026-07-03T08:14:32Z",
  "severity": "P1",
  "business\_impact\_score": 97,
  "root\_cause": "RootCauseObject",
  "related\_anomalies": \["anomaly\_id\_1", "anomaly\_id\_2"],
  "deduplicated\_count": 6,
  "sla\_breach\_risk": "HIGH",
  "assigned\_to": "auto-remediation",
  "status": "OPEN"
}
```

### SimulaXResult (from Layer 8 SimulaX)

```json
{
  "simulation\_id": "SIM-20260703-00481",
  "mode": "REMEDIATION\_SIMULATION",
  "proposed\_action": {
    "type": "ROLLBACK",
    "target": "payments-analytics",
    "from\_version": "v2.1.4",
    "to\_version": "v2.1.3"
  },
  "predicted\_outcome": {
    "resolution\_confidence": 0.91,
    "recovery\_time\_minutes": 8,
    "side\_effects": \["payments-reporting unavailable (v2.1.4 only)"],
    "revenue\_recovery\_usd": 84200
  },
  "risk\_score": 0.12,
  "recommendation": "PROCEED"
}
```

### ConfigDriftEvent (from Cross-Cutting Config Drift Engine)

```json
{
  "drift\_id": "DRF-2026-07-001",
  "drift\_source": "kubernetes",
  "detection\_method": "git\_diff",
  "drifted\_entity": "payments-analytics-deployment",
  "expected\_state": { "replicas": 5, "image": "v2.1.3" },
  "actual\_state": { "replicas": 2, "image": "v2.1.4" },
  "remediation\_tool": "argocd",
  "remediation\_action": "self-heal-sync",
  "confidence": 0.98,
  "timestamp": "2026-07-03T08:10:55Z"
}
```

### SecurityAnomalySignal (from Layer 9 SentinelPlane)

```json
{
  "attack\_type": "BRUTE\_FORCE",
  "entity\_id": "auth-service",
  "severity": "HIGH",
  "confidence": 0.92,
  "evidence\_logs": \["Failed login from 10.0.0.5 x 50 in 60s"],
  "recommended\_action": "BLOCK\_IP",
  "source\_ip": "10.0.0.5",
  "timestamp": "2026-07-03T08:15:00Z"
}
```

### ActionResult (from Layer 7 AutoHeal)

```json
{
  "action\_type": "ROLLBACK",
  "entity\_id": "payments-analytics",
  "success": true,
  "output": "Rolled back to v2.1.3 successfully",
  "error": null,
  "execution\_time\_seconds": 12.5,
  "executed\_at": "2026-07-03T08:16:30Z",
  "triggered\_by": "auto",
  "incident\_id": "INC-2026-07-001",
  "simulaX\_validated": true,
  "simulation\_id": "SIM-20260703-00481"
}
```

\---

## Kafka Topics Reference

|Topic Name|Producer (Layer)|Consumer (Layer)|
|-|-|-|
|`omniwatch.telemetry.raw`|Layer 2: GhostCollector|Layer 3: StreamForge|
|`omniwatch.metrics.raw`|Layer 3: StreamForge|Layer 4: NexusStore|
|`omniwatch.logs.raw`|Layer 3: StreamForge|Layer 4: NexusStore|
|`omniwatch.traces.raw`|Layer 3: StreamForge|Layer 4: NexusStore|
|`omniwatch.topology.deltas`|Layer 3: StreamForge|Layer 5: TopoBrain|
|`omniwatch.anomalies.detected`|Layer 6: NeuroEngine|Layer 6: Prioritization|
|`omniwatch.incidents.created`|Layer 6: NeuroEngine|Layer 7: AutoHeal, Layer 10: Learning|
|`omniwatch.remediation.actions`|Layer 7: AutoHeal|Layer 10: Learning, Layer 11: NexusUX|
|`omniwatch.security.events`|Layer 9: SentinelPlane|Layer 6: NeuroEngine|
|`omniwatch.config.drift`|Cross-Cutting: Config Drift|Layer 7: AutoHeal|
|`omniwatch.simulation.results`|Layer 8: SimulaX|Layer 7: AutoHeal, Layer 11: NexusUX|

\---

## Storage Reference

### ClickHouse Tables (database: omniwatch)

|Table|Contains|Primary Query Pattern|
|-|-|-|
|`metrics`|All time-series metrics (windowed)|By entity\_id + time range|
|`logs`|All log events|By entity\_id + log\_level|
|`traces`|All distributed spans|By trace\_id + service|
|`anomalies`|Detected anomaly records|By status + timestamp|
|`incidents`|Full incident records|By severity + status|
|`profiles`|Continuous profiling data|By entity\_id + time|
|`pending\_approvals`|Awaiting human approval|By status = 'pending'|
|`knowledge\_base`|Resolved incident outcomes|By root\_cause\_entity\_type|
|`simulations`|SimulaX simulation results|By simulation\_id + mode|
|`config\_drifts`|Configuration drift events|By drift\_source + status|
|`cost\_carbon`|Per-entity cost + carbon data|By entity\_id + time|

### Kuzu Node Types (Graph Store)

|Label|Properties|
|-|-|
|`:Service`|id, name, type, criticality, cloud\_provider, status, anomaly\_score, last\_seen|
|`:Process`|id, name, type, container\_id, pod\_id, host\_id, anomaly\_score|
|`:Host`|id, name, type, cloud\_provider, region, cpu, memory, anomaly\_score|
|`:Infrastructure`|id, name, type, cloud\_provider, status, anomaly\_score|
|`:Database`|id, name, type, cloud\_provider, status, anomaly\_score|
|`:GenAIService`|id, name, model, provider, token\_cost, latency, anomaly\_score|
|`:BusinessTransaction`|id, name, revenue\_impact, sla\_target, error\_budget|
|`:CostCenter`|id, name, hourly\_cost\_usd, carbon\_grams\_per\_hour|

### Kuzu Relationship Types

|Relationship|Properties|
|-|-|
|`:CALLS`|latency\_p50, latency\_p95, latency\_p99, error\_rate|
|`:READS\_FROM`|query\_type, avg\_duration\_ms|
|`:DEPENDS\_ON`|dependency\_type, criticality|
|`:DEPLOYED\_ON`|deployment\_version, deployed\_at|
|`:HOSTED\_BY`|cost\_center\_id, hourly\_cost|
|`:INFERRED\_BY`|causal\_score, confidence, method|

### MinIO Buckets

|Bucket|Contents|
|-|-|
|`omniwatch-telemetry-archive`|Aged telemetry > 90 days (Parquet)|
|`omniwatch-incidents`|Full incident JSON records|
|`omniwatch-audit-logs`|All remediation + drift action logs|
|`omniwatch-ml-datasets`|Historical data for model training|
|`omniwatch-runbooks`|Generated runbooks and playbooks|
|`omniwatch-compliance`|SOC2/ISO27001 evidence packages|
|`omniwatch-simulations`|SimulaX simulation results archive|

\---

## Current Build Phase

|Phase|Name|Layers|Status|
|-|-|-|-|
|Phase 1|Foundation|Layer 2 (GhostCollector v1), Layer 3 (StreamForge v1), Layer 4 (NexusStore v1), Layer 5 (TopoBrain v1), Layer 11 (NexusUX v1)|← START HERE|
|Phase 2|Intelligence|Layer 5 (TopoBrain v2), Layer 6 (NeuroEngine), Layer 4 (NexusStore v2), Layer 3 (StreamForge v2), Layer 9 (SentinelPlane v1)||
|Phase 3|Autonomy|Layer 8 (SimulaX), Layer 7 (AutoHeal v3), Config Drift Engine, Layer 2 (GhostCollector v2), Layer 5 (TopoBrain v3)||
|Phase 4|Ecosystem|Self-hosted, Compliance, Multi-region, Integrations, Mobile||

**Check `docs/Build-Plan.md` for the full phase-by-phase roadmap.**

\---

## Gaps to Implement

### GAP 1 — Entity Resolution Layer

```
File:     ingestion/stream\_forge/entity\_resolution.py
Status:   Not implemented
What:     Maps volatile telemetry IDs (pod UIDs, container IDs, IPs) to stable entities
Problem:  Without it, every pod restart = new node = broken topology = bad RCA
Input:    omniwatch.telemetry.raw (Kafka topic)
Output:   Stabilized entity IDs → ClickHouse + Kuzu
Technology: Apache Flink stateful keyed stream + RocksDB
```

### GAP 2 — Windowing Layer

```
File:     ingestion/stream\_forge/windowing\_layer.py
Status:   Not implemented
What:     Converts raw irregular telemetry into aligned, ML-ready feature vectors
Problem:  Without it, Merlion and PyTorch models get misaligned data → false anomalies
Input:    Entity-resolved telemetry streams
Output:   ML-ready feature vectors → ClickHouse
Technology: Apache Flink tumbling windows + feature engineering
```

### GAP 3 — Configuration Drift Engine

```
File:     remediation/config\_drift/
Status:   Not implemented
What:     Detects and auto-remediates drift across K8s, OS, Cloud, Git layers
Problem:  System detects anomalies but cannot fix configuration mismatches
Input:    Git diffs, K8s Watch API, Terraform state diffs
Output:   Remediation actions via ArgoCD, Ansible EDA, Terraform
Technology: ArgoCD + Ansible EDA + Terraform
```

### GAP 4 — Incident Aggregation

```
File:     ai/causal/problem\_assembler.py
Status:   Not implemented
What:     Groups many related alerts/anomalies into one meaningful incident
Problem:  Without it, 1 failure = 200 alerts = alert fatigue
Input:    Anomaly signals + topology context
Output:   Single deduplicated IncidentRecord
Technology: Kuzu graph-based grouping + time window correlation
```

### GAP 5 — Security Signal Classifier

```
File:     security/runtime\_security.py
Status:   Not implemented
What:     Dedicated security anomaly detection separate from performance
Problem:  Security events mixed with performance signals → no clear security RCA
Input:    Security telemetry (SIEM, auth logs, firewall)
Output:   SecurityAnomalySignal → NeuroEngine
Technology: eBPF LSM hooks + pattern matching
```

### GAP 6 — Grounded Generation System

```
File:     ai/generative/grounded\_llm\_client.py
          ai/generative/output\_validator.py
Status:   Not implemented
What:     Prevents LLM hallucination by enforcing evidence-backed output
Problem:  LLMs can generate ungrounded root cause summaries
Input:    RootCauseObject + evidence chain
Output:   Validated incident summary, runbook, report
Technology: vLLM + strict system prompt + entity validation
```

### GAP 7 — Compliance Report Generator

```
File:     learning/compliance\_reporter.py
Status:   Not implemented
What:     Automated SOC2/ISO27001 evidence packages
Problem:  Manual compliance reporting is slow and error-prone
Input:    ClickHouse incidents + MinIO audit logs
Output:   Markdown compliance report → omniwatch-compliance bucket
Technology: Python + Jinja2 templates
```

### GAP 8 — SimulaX Digital Twin

```
File:     simulation\_engine/digital\_twin.py
Status:   Not implemented
What:     Continuously updated model of production for what-if simulation
Problem:  No system can predict outcome of changes before applying them
Input:    NexusStore metrics + TopoBrain topology + NeuroEngine models
Output:   Digital twin state + simulation results
Technology: SimPy + Redis + Optuna (Bayesian calibration)
```

\---

## Local Infrastructure

### Start Everything

```bash
docker-compose up -d
```

### Service Endpoints

|Service|URL|Credentials|
|-|-|-|
|Kuzu Explorer|(embedded, no browser UI)|N/A|
|MinIO Console|http://localhost:9002|minioadmin / minioadmin|
|ClickHouse|localhost:9000|default / (no password)|
|Kafka|localhost:9092|none|
|OPA|http://localhost:8181|none|
|Ollama API|http://localhost:11434|none|
|Dashboard Backend|http://localhost:8000|none|
|Dashboard Frontend|http://localhost:3000|none|

\---

## Coding Standards

### File Header (All Python Files)

```python
"""
OmniWatch 2.0 — <Layer Name>
Component: <Component Name>
Layer: <Layer Number>
Phase: <Phase Number>
Purpose: <One line description>
Inputs: <What data comes in>
Outputs: <What data goes out>
"""
```

### Naming Conventions

|Type|Convention|Example|
|-|-|-|
|Python files|`snake\_case.py`|`entity\_resolution.py`|
|Python classes|`PascalCase`|`RootCauseBuilder`|
|Python functions|`snake\_case()`|`build\_root\_cause()`|
|Kafka topics|`omniwatch.domain.event`|`omniwatch.telemetry.raw`|
|Kuzu labels|`PascalCase`|`:Service`, `:GenAIService`|
|Kuzu relations|`UPPER\_SNAKE\_CASE`|`:CALLS`, `:DEPENDS\_ON`|
|ClickHouse tables|`snake\_case`|`metrics`, `anomalies`|
|MinIO buckets|`kebab-case`|`omniwatch-incidents`|
|React components|`PascalCase.tsx`|`SREMode.tsx`|
|React pages|`PascalCase.tsx`|`IncidentExplorer.tsx`|

### Every Service Must Have

1. `Dockerfile`
2. `README.md` explaining inputs, outputs, how to run
3. Environment variables loaded from `.env` (never hardcoded)
4. Logging to stdout in structured JSON format
5. Health check endpoint (FastAPI: `GET /health`)

### Git Commit Format

```
phase<N>: <component> — <what you built>
```

Examples:

```
phase1: ghost\_collector — add eBPF HTTP/gRPC capture
phase1: entity\_resolution — implement volatile ID stabilization
phase2: neuroengine\_causal — implement GNN + Granger root cause
gap3: config\_drift — add ArgoCD self-heal integration
```

\---

## Agent Instructions

### When Adding a New Component

```
1. Read the corresponding section in docs/Build-Plan.md

2. Understand the component's:
   - Input (which Kafka topic or database it reads from)
   - Output (what it produces and where it sends it)
   - Data contract (which schema from Key Data Contracts)

3. Create the file in the correct directory per Repository Structure

4. Add the file header with Layer, Phase, Purpose, Inputs, Outputs

5. Write the implementation

6. Update the directory README.md

7. Run integration tests with external telemetry data
```

### When Modifying Existing Components

```
1. Check which downstream components consume this component's output
   (use Kafka Topics Reference)

2. Do NOT change output schema without updating all consumers

3. Do NOT change ClickHouse table schema without updating schema.sql

4. Do NOT change Kuzu node properties without updating
   ai/causal/causal\_graph\_traversal.py
```

### When Unsure About Architecture

```
Read in this order:
1. docs/New-System-Architecture.md       (11-layer spec)
2. docs/DataFlow.md                       (end-to-end flow)
3. docs/Build-Plan.md                     (phase-by-phase roadmap)
4. This AGENTS.md (Key Data Contracts)    (data schemas)

Do NOT invent new Kafka topics, storage tables, or data schemas.
Use only what is defined in this file and the architecture docs.
```

### Simulation-First Rule

```
All components must be testable using external telemetry data
received from the dedicated simulation server.

No component should require real AWS, Azure, or GCP credentials.
If a component needs cloud data, it must have a simulation fallback.
```

\---

## Integration Test Scenarios

Run after completing each phase to verify correct behavior:

|Scenario|Expected Outcome|
|-|-|
|Normal telemetry ingestion|No incidents created|
|Database cascade anomaly|P1 incident, root cause = postgres, auto-remediation|
|Memory leak anomaly|P2 incident, root cause = background-worker|
|Security attack pattern|Security P2, brute force detected, IP block recommended|
|Configuration drift|UNAUTHORIZED\_CONFIG\_CHANGE detected, ArgoCD self-heal|
|LLM cost spike|GenAI cost anomaly detected|
|Alert storm (10x rapid)|Only 1 incident, deduplicated\_count = 10|
|SimulaX validation|Shadow simulation runs before Tier 3 execution|

\---

## Demo Flow (5 Minutes — IEEE YESIST12 2026)

```
Minute 1 — Show NexusUX dashboard (Layer 11: SRE Mode)
            Normal system state, 8-layer topology visible

Minute 2 — Inject database\_cascade anomaly (from external simulation server)
            Real-time detection via GhostCollector (Layer 2)
            → StreamForge Entity Resolution stabilizes IDs (Layer 3)
            → TopoBrain shows 8-layer topology updating (Layer 5)
            → NeuroEngine detects + traces root cause (Layer 6)

Minute 3 — Show Incident Explorer with evidence chain
            Root cause path: Frontend → Checkout → Payment → DB → Host
            Confidence score: 94%
            Blast radius: 12,400 users affected

Minute 4 — Show auto-remediation executing
            SimulaX shadow simulation (Layer 8) → confidence 91%
            AutoHeal Tier 3 executes rollback (Layer 7)
            Config Drift Engine restores Git state (Cross-Cutting)

Minute 5 — Show generated outputs
            GenAI incident summary + runbook (Layer 6)
            Compliance report (Layer 10)
            Knowledge Base updated for future recommendations
```

\---

## Key Differentiators

|Feature|Dynatrace|OmniWatch 2.0|
|-|-|-|
|Collection|Process injection|eBPF-native (<0.5% CPU)|
|Topology|5 tiers|8 layers (adds GenAI, Business, Cost)|
|AI Root Cause|Opaque|Full evidence chain + confidence score|
|Digital Twin|None|4 simulation modes (SimulaX)|
|Self-Hosted|None|Full parity|
|GenAI Observability|None|Native LLM tracking|
|Cost/Carbon|None|Per-entity tracking|
|Config Drift|Indicates only|Auto-remediates (ArgoCD/Ansible/Terraform)|
|BYOM|Fixed LLM|Any model (GPT/Claude/Gemini/Llama)|
|Differential Analysis|None|DiffEngine (cross-signal BubbleUp)|

\---

## Competition Context

|Field|Value|
|-|-|
|**Competition**|IEEE YESIST12 2026 — IEngage Track|
|**Problem**|Proactive Anomaly Detection Intelligence|
|**Submitted by**|2nd year CSE student|
|**Approach**|Fully open-source, zero vendor lock-in, locally runnable|
|**Cost**|$0 (all open-source stack)|

\---

## Phase Summary Protocol

**After completing every phase, save a phase summary to:**

```
E:\\Project-OmniWatch-2.0\\Project-Details\\Phase-Summaries\\
```

**File naming:** `Phase-<N>-Summary.md`

**Required sections in each summary:**

1. Phase Overview (what was built)
2. Components Completed (list with Layer numbers)
3. Data Contracts Implemented
4. Integration Test Results
5. Gaps Addressed
6. Challenges \& Solutions
7. Next Phase Preview

\---

## GitHub Maintenance Rules

1. **Never commit** `.env` files, API keys, tokens, or credentials
2. **Never commit** `node\_modules/`, `\_\_pycache\_\_/`, `.venv/`, or build artifacts
3. **Always** use meaningful commit messages following `phase<N>: <component>` format
4. **Always** update `README.md` when adding new components
5. **Always** create feature branches for new phases: `git checkout -b phase<N>-<name>`
6. **Always** run tests before pushing to `main`
7. **Tag releases** for each phase completion: `git tag -a phase<N>-v1.0 -m "Phase N complete"`
8. **Protect `main`** branch — require PR review before merge

\---

*Document Version: 2.0 | Generated: July 2026 | Classification: Internal R\&D*

