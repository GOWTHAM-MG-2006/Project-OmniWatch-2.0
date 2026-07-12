# OmniWatch — New System Architecture

## Complete System Design Specification

> **Version:** 2.0
> **Date:** July 2026
> **Classification:** Internal R&D / Architecture Blueprint
> **Governing Principle:** Every design decision outperforms Dynatrace's depth, Datadog's breadth, Grafana's openness, and Honeycomb's developer ergonomics.

---

## TABLE OF CONTENTS

1. [Core Architectural Philosophy](#1-core-architectural-philosophy)
2. [System Overview](#2-system-overview)
3. [Layer 1 — Data Sources](#3-layer-1--data-sources)
4. [Layer 2 — GhostCollector (eBPF-Native Collection)](#4-layer-2--ghostcollector)
5. [Layer 3 — StreamForge (Intelligent Ingest Pipeline)](#5-layer-3--streamforge)
6. [Layer 4 — NexusStore (Unified Data Lakehouse)](#6-layer-4--nexusstore)
7. [Layer 5 — TopoBrain (Causal Knowledge Graph)](#7-layer-5--topobrain)
8. [Layer 6 — NeuroEngine (Hypermodal AI)](#8-layer-6--neuroengine)
9. [Layer 7 — AutoHeal (Autonomous Remediation)](#9-layer-7--autoheal)
10. [Layer 8 — SimulaX (Digital Twin & Simulation)](#10-layer-8--simulax)
11. [Layer 9 — SentinelPlane (Security Observability)](#11-layer-9--sentinelplane)
12. [Layer 10 — Continuous Learning](#12-layer-10--continuous-learning)
13. [Layer 11 — NexusUX (Role-Adaptive Experience)](#13-layer-11--nexusux)
14. [Configuration Drift Engine (Cross-Cutting)](#14-configuration-drift-engine)
15. [Technology Stack](#15-technology-stack)
16. [KPI Benchmarks](#16-kpi-benchmarks)
17. [Competitor Gap Registry](#17-competitor-gap-registry)

---

## 1. Core Architectural Philosophy

### The Five Founding Principles

| Principle | Statement |
|-----------|-----------|
| **P1: Causality + Evidence** | Every insight grounded in traceable causal chain. No black-box decisions. |
| **P2: Topology Is Truth** | 8-layer causal knowledge graph updated in <500ms. |
| **P3: Zero Friction** | Zero code changes for any supported target. eBPF-first collection. |
| **P4: Open by Default** | Full OTel-native. NQL is superset of PromQL+LogQL+SQL. |
| **P5: Prevention Before Detection** | System operates at Predict, Simulate, and Prevent levels. |

---

## 2. System Overview

### 11-Layer Architecture

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                              OMNIWATCH 2.0 ARCHITECTURE                              ║
╠══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                      ║
║  ┌────────────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 11: NEXUSUX (Role-Adaptive Experience)                                  │  ║
║  │  AI-First | SRE | Developer | Executive | Security                            │  ║
║  └──────────────────────────────────────┬─────────────────────────────────────────┘  ║
║                                         │                                            ║
║  ┌──────────────┐ ┌──────────────┐  ┌───┴──────────┐ ┌─────────────────────────┐     ║
║  │  LAYER 8     │ │  LAYER 9     │  │  LAYER 7     │ │  LAYER 6                │     ║
║  │  SIMULAX     │ │  SENTINEL    │  │  AUTOHEAL    │ │  NEUROENGINE            │     ║
║  │  Digital Twin│ │  PLANE       │  │  Autonomous  │ │  Causal + Predictive    │     ║
║  │  What-If     │ │  Security    │  │  Remediation │ │  + Generative + Diff    │     ║
║  │  Simulation  │ │  Observ.     │  │  Engine      │ │  (BYOM Supported)       │     ║
║  └──────┬───────┘ └──────┬───────┘  └──────┬───────┘ └───────────┬─────────────┘     ║
║         │                │                 │                     │                   ║
║  ┌──────▼────────────────▼─────────────────▼─────────────────────▼───────────────┐   ║
║  │  LAYER 5: TOPOBRAIN (8-Layer Causal Knowledge Graph)                          │   ║
║  │  Cost+Carbon | Infra | Hosts | Processes | Services | Apps | GenAI | Business │   ║
║  └───────────────────────────────────────┬───────────────────────────────────────┘   ║
║                                          │                                           ║
║  ┌───────────────────────────────────────▼────────────────────────────────────────┐  ║
║  │  LAYER 4: NEXUSSTORE (Unified Data Lakehouse)                                  │  ║
║  │  Hot (Arrow) | Warm (ClickHouse) | Cold (Parquet/Iceberg) | Graph (Kuzu)       │  ║
║  └───────────────────────────────────────┬────────────────────────────────────────┘  ║
║                                          │                                           ║
║  ┌───────────────────────────────────────▼────────────────────────────────────────┐  ║
║  │  LAYER 3: STREAMFORGE (Intelligent Ingest Pipeline)                            │  ║
║  │  Entity Resolution | Windowing | Tail Sampling | PII Engine | Cost/Carbon      │  ║
║  └───────────────────────────────────────┬────────────────────────────────────────┘  ║
║                                          │                                           ║
║  ┌───────────────────────────────────────▼────────────────────────────────────────┐  ║
║  │  LAYER 2: GHOSTCOLLECTOR (eBPF-Native Collection)                              │  ║
║  │  eBPF Kernel | Bytecode Inject | OTLP Receiver | Cloud API | RUM | LLM         │  ║
║  └───────────────────────────────────────┬────────────────────────────────────────┘  ║
║                                          ↑                                           ║
║  ┌───────────────────────────────────────▼────────────────────────────────────────┐  ║
║  │  LAYER 1: DATA SOURCES                                                         │  ║
║  │  K8s | VMs | Bare Metal | Serverless | Mainframes | Browsers | LLM APIs        │  ║
║  └────────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                      ║
║  ┌────────────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 10: CONTINUOUS LEARNING & KNOWLEDGE BASE                               │  ║
║  │  Feedback Loop | Pattern Mining | Recommendations | Incident KB                │  ║
║  └────────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                      ║
║  ┌────────────────────────────────────────────────────────────────────────────────┐  ║
║  │  CONFIGURATION DRIFT ENGINE (Cross-Cutting)                                    │  ║
║  │  Git Diff | ArgoCD | Ansible | Terraform | Policy Gate                         │  ║
║  └────────────────────────────────────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. Layer 1 — Data Sources

**All monitored infrastructure and applications producing telemetry.**

### Supported Sources

| Category | Examples |
|----------|----------|
| **Cloud Platforms** | AWS (EC2, EKS, RDS, Lambda, CloudWatch), Azure (VMs, AKS, Azure SQL), GCP (Compute Engine, GKE, Cloud SQL) |
| **Container Platforms** | Kubernetes (Pods, Services, Deployments, Ingress, Helm) |
| **Application Sources** | Microservices, REST APIs, Web Applications, Backend Services |
| **Observability Sources** | Logs, Metrics, Traces, Events |
| **Security Sources** | SIEM Events, Authentication Logs, Security Alerts |
| **LLM/AI Sources** | OpenAI, Anthropic, Google Gemini, Ollama, vLLM |
| **Infrastructure Sources** | Databases, Message Queues, Load Balancers, Virtual Machines |

### Output
Produces raw telemetry: Logs, Metrics, Traces, Security Events, LLM Call Data

---

## 4. Layer 2 — GhostCollector

**eBPF-native, zero-overhead collection engine with 6 collection modes.**

### Collection Modes

| Mode | Method | Coverage |
|------|--------|----------|
| **Mode 1: eBPF Kernel Probes** | kprobes, uprobes, tracepoints, XDP/TC, LSM hooks | HTTP/gRPC/SQL, network, file I/O, process lifecycle |
| **Mode 2: Runtime Bytecode Injection** | JVMTI, CLR Profiling API, V8 hooks | Java, .NET, Node.js, Python, PHP |
| **Mode 3: OTLP Receiver** | OTLP/gRPC + OTLP/HTTP | OTel-instrumented apps, Prometheus, ES |
| **Mode 4: Cloud API Polling** | AWS/Azure/GCP APIs, K8s Watch | Cloud resources, cost APIs, carbon APIs |
| **Mode 5: Real User Monitoring** | Auto-injected JS | Core Web Vitals, Session Replay |
| **Mode 6: LLM/GenAI Observability** | Framework hooks (LangChain, LlamaIndex) | Token count, latency, cost, agent chains |

### Key Features

- **CPU overhead target:** < 0.5% (vs Dynatrace ~1-3%)
- **In-agent edge computing:** Only anomalous spans exported
- **Self-healing watchdog:** Auto-restart, CPU budget enforcer
- **Windows support:** Via ebpf-for-windows

### Technology

| Component | Technology |
|-----------|-----------|
| eBPF runtime | libbpf + CO-RE (Linux 5.8+) |
| eBPF programs | C (eBPF) + Rust (controller) |
| Agent language | Go |
| Serialization | Protocol Buffers + MessagePack |

---

## 5. Layer 3 — StreamForge

**Intelligent ingest pipeline with Entity Resolution, Windowing, and adaptive sampling.**

### StreamForge Architecture

```
Stage 1: RECEIPT & VALIDATION
  → Multi-protocol: OTLP, PromQL, ES Bulk, Kafka
  → Schema validation, mTLS, rate limiting

Stage 2: ENRICHMENT ENGINE
  → Semantic Dictionary (field normalization)
  → Entity Resolution Layer (stabilize volatile IDs → stable entities)
  → Cost enrichment (per-request cloud cost)
  → Carbon enrichment (kg CO₂ estimate)
  → Geo-enrichment, SLO context

Stage 3: ADAPTIVE INTELLIGENCE
  → Tail-Based Causal Sampling (keep errors, drop normal)
  → Anomaly-Prioritized Routing (anomalous → hot, normal → cold)
  → Privacy-by-Default PII Engine (regex + ML detection)

Stage 4: WINDOWING LAYER
  → Flink tumbling windows (1-min aggregates)
  → Feature engineering (rolling mean, z-score, rate of change)
  → Missing data handling (interpolation, forward-fill)
  → ML-ready feature vectors

Stage 5: TOPOLOGY DELTA PUBLISHER
  → Publishes topology edges to TopoBrain (<500ms latency)

Stage 6: MULTI-DESTINATION ROUTING
  → Primary: NexusStore | Mirror: S3/GCS | Forward: OTLP | Archive: Parquet
```

### Entity Resolution Layer (New Addition)

**Purpose:** Maps volatile telemetry IDs (pod UIDs, container IDs, IP addresses) to stable logical entities.

| Problem | Solution |
|---------|----------|
| Pods restart with new IDs | Maps pod-123, pod-456 → payment-service |
| Auto-scaling creates duplicates | Deduplicates instances under logical entity |
| Services move between nodes | Tracks lifecycle across relocations |

### Windowing Layer (New Addition)

**Purpose:** Converts raw irregular telemetry into aligned, ML-ready feature vectors.

| Step | Action |
|------|--------|
| Time Windowing | CPU every 5s → 1-min aggregates (mean, max, p95) |
| Time Alignment | Align CPU (5s), DB latency (10s), Request rate (1s) → same timestamps |
| Feature Engineering | Rolling mean, rolling std, z-score, error ratio, saturation % |
| Missing Data Handling | Interpolation, forward-fill, sparse entity flagging |

### Technology

| Component | Technology |
|-----------|-----------|
| Message backbone | Apache Kafka |
| Stream processor | Apache Flink |
| Entity Resolution | Flink stateful keyed stream + RocksDB |
| PII scanner | Custom ML + Microsoft Presidio |

---

## 6. Layer 4 — NexusStore

**Unified data lakehouse with 4 storage tiers and NQL query language.**

### Storage Tiers

| Tier | Technology | Access Time | Data |
|------|-----------|-------------|------|
| **Hot** | Apache Arrow (in-memory) | Sub-ms | Last 2-6 hours, all anomalous signals |
| **Warm** | ClickHouse cluster | Single-digit ms | Last 90 days, all signals |
| **Cold** | Parquet + Iceberg on S3/GCS | Seconds | 13+ months, petabyte-scale |
| **Graph** | Apache Kuzu | Millisecond | Entity nodes, dependency edges |

### Five Unified Data Models

1. **Time Series** — Metrics (counters, gauges, histograms)
2. **Event Store** — Logs, deployment events, alerts
3. **Trace Store** — Distributed spans, PurePath-equivalent
4. **Graph Store** — Entity topology, dependency relationships
5. **Profile Store** — Continuous CPU/memory/heap flame graphs

### NQL — NexusQL

```sql
-- Cross-signal topology-aware query
FETCH services
  DOWNSTREAM OF "payment-service" IN topology
  WHERE p99_latency > baseline * 1.5
  WITHIN last 30m
JOIN logs ON entity.id WHERE log.severity = "ERROR"
JOIN profiles ON entity.host_id WHERE profile.cpu_percent > 70
RETURN entity.name, p99_latency, error_count = COUNT(logs),
       top_cpu_frames = TOP(profiles.frames, 5)

-- PromQL compatibility
rate(http_requests_total{service="checkout"}[5m])

-- Cost + performance correlation
FETCH services WHERE p99_latency > 500ms WITHIN last 1h
ANNOTATE hourly_cost = cost.estimate_usd, carbon_g = carbon.estimate_grams
```

---

## 7. Layer 5 — TopoBrain

**8-layer causal knowledge graph with <500ms update latency.**

### 8-Layer Entity Model

```
LAYER 8: BUSINESS TRANSACTIONS (Revenue, conversion, SLA)
         ↕
LAYER 7: GenAI / LLM SERVICES (Models, agents, RAG, vector DBs)
         ↕
LAYER 6: APPLICATIONS (Web, SPAs, CLIs)
         ↕
LAYER 5: SERVICES (APIs, microservices, workers, queues)
         ↕
LAYER 4: PROCESSES (JVM, container, pod, worker thread)
         ↕
LAYER 3: HOSTS (EC2, VM, bare metal, K8s node, Lambda)
         ↕
LAYER 2: INFRASTRUCTURE (VPC, subnet, AZ, K8s cluster)
         ↕
LAYER 1: COST + CARBON (Cloud account, cost center, CO₂)
```

### Data Sources → TopoBrain

| Source | Edge Type |
|--------|-----------|
| GhostCollector eBPF flows | Service-to-service TCP edges |
| GhostCollector runtime inject | Method-level call edges |
| StreamForge topology deltas | Edge creation/update/expiry |
| Kubernetes Watch API | Pod/Node/Service/Ingress |
| Cloud API polling | VPC/SG/LB/Lambda |
| RUM beacon data | Browser-session → service |
| OTel trace spans | Service call edges |
| Deployment events | "deployed at T" annotations |
| Cost API polling | Service → cost_center |

### Key Features

| Feature | Description |
|---------|-------------|
| Live dependency graph | <500ms update latency |
| 8-layer entity model | Adds GenAI, Business, Cost layers |
| Drift detection | Runtime topology vs. declared architecture |
| Blast radius calculator | All entities impacted + confidence % |
| Cost topology | Hourly cost per entity |
| Carbon topology | g CO₂/hour per entity |
| GenAI chain map | LLM → agent → tool → vector DB |

---

## 8. Layer 6 — NeuroEngine

**Hypermodal AI with 4 operating modes.**

### Mode 1: Causal Detection Engine (Deterministic)

```
Step 1: Dynamic Baseline (Holt-Winters + ARIMA)
  → Per-entity, per-metric, per-time-of-week

Step 2: Multi-Signal Anomaly Detection
  → Metrics, Logs, Traces, Network, Code, Topology anomalies

Step 3: Causal Graph Traversal
  → Query TopoBrain for dependencies
  → Granger Causality test
  → GNN (CausalGNN) for inter-service causal weights
  → Root Cause = highest causal score + earliest time

Step 4: Problem Assembly
  → Group anomalies → ONE Problem
  → Evidence chain + confidence score + blast radius
```

### Mode 2: Predictive Engine (ML Forecasting)

- Prophet (seasonality) + LSTM (non-linear patterns)
- Forecasts: disk exhaustion, memory leak, CPU saturation
- Horizon: 1h, 24h, 7d per entity
- Auto-triggers AutoHeal for predictive issues

### Mode 3: Generative AI Layer (BYOM)

- NL Query: "Why is checkout slow?" → NQL + English answer
- Problem Summary grounded in Causal Engine output
- Postmortem Generator, Code Fix Suggestion, Dashboard Generator
- **BYOM:** GPT-4o, Claude 3.5, Gemini, Llama 3, custom models
- **Grounding Guardrail:** Every output prefixed with evidence record list

### Mode 4: Differential Analysis Engine (DiffEngine)

- Based on Honeycomb BubbleUp, extended
- Compares bad-set vs normal-set across ALL signal types
- Auto cross-links to TopoBrain for causal context
- Outputs ranked causal hypothesis

### Root Cause Output Format

```json
{
  "problem_id": "PRB-20260703-09421",
  "confidence": 0.94,
  "severity": "CRITICAL",
  "root_cause": {
    "entity": "postgres-payments-primary",
    "metric": "query_execution_time_p99",
    "deviation": "1,240ms vs baseline 38ms (+3168%)",
    "causal_score": 0.94
  },
  "evidence_chain": [ /* 4 steps with timestamps and methods */ ],
  "blast_radius": [ /* impacted entities + affected users */ ],
  "business_impact": {
    "affected_users": 12400,
    "estimated_revenue_at_risk_usd_per_hour": 84200
  }
}
```

---

## 9. Layer 7 — AutoHeal

**Autonomous remediation with 5 autonomy tiers.**

### Autonomy Tiers

| Tier | Name | Behavior |
|------|------|----------|
| **0** | Observe Only | Detect + analyze, no action |
| **1** | Notify + Recommend | Notify on-call, suggest top 3 fixes |
| **2** | Auto-Execute (Low-Risk) | Pod restart, scale-out, circuit breaker |
| **3** | Fully Autonomous (SimulaX-Validated) | Generate strategy → SimulaX validate → Execute |
| **4** | Predictive Autonomous | Act BEFORE user impact |

### AutoHeal Workflow

```
NeuroEngine Problem Event
  → OPA Policy Engine (Rego rules)
  → IF confidence > 95% AND severity = P1 → Auto-Remediate
  → IF medium confidence → Approval Workflow → Human sign-off
  → IF Tier 3+ → SimulaX Shadow Simulation → Execute if validated
  → Action Library (restart, rollback, scale, rotate)
  → Execution Engine (K8s API, AWS/Azure/GCP APIs)
  → Rollback auto-generated before execution
  → Full audit log
```

### Configuration Drift Integration (New Addition)

```
Drift Detected (Git diff, K8s config, cloud state)
  → Route by layer:
    K8s Drift → ArgoCD (self-heal sync)
    OS Drift → Ansible (EDA rulebook + playbook)
    Cloud Drift → Terraform (state reconciliation)
    Git Drift → Auto-revert commit
  → Approval gate for high-impact Terraform actions
```

---

## 10. Layer 8 — SimulaX

**Digital twin & what-if simulation engine. No competitor has this.**

### Architecture

```
Digital Twin (Continuously Updated)
  ← NexusStore: real-time metrics
  ← TopoBrain: live dependency graph
  ← NeuroEngine: learned behavioral models
  ← GhostCollector: process-level consumption

Model Components:
  • Per-service queuing model (M/M/c)
  • Per-host resource contention model
  • Network propagation delay model
  • Cascade failure model
  • Cost consumption model
  • SLO compliance model
```

### 4 Simulation Modes

| Mode | Trigger | Output |
|------|---------|--------|
| **Remediation** | AutoHeal proposes fix | Predicted outcome + confidence + risk score |
| **Capacity** | "What if traffic doubles?" | Capacity report + pre-scaling actions |
| **Deployment** | CI/CD pre-deploy gate | Risk score → Block/Warn/Approve |
| **Chaos** | User defines scenario | Predicted blast radius + resilience gaps |

### SimulaX Result Object

```json
{
  "simulation_id": "SIM-20260703-00481",
  "mode": "REMEDIATION_SIMULATION",
  "predicted_outcome": {
    "root_cause_resolution_confidence": 0.91,
    "estimated_recovery_time_minutes": 8,
    "side_effects": [ { "entity": "payments-reporting", "severity": "LOW" } ],
    "estimated_revenue_recovery_usd": 84200
  },
  "risk_score": 0.12,
  "recommendation": "PROCEED"
}
```

---

## 11. Layer 9 — SentinelPlane

**Unified security observability — eBPF runtime security + CVE reachability + CSPM.**

### Components

| Component | Description |
|-----------|-------------|
| **Runtime Security Detection** | eBPF LSM hooks: privilege escalation, container escape, RCE, C2, exfiltration |
| **Vulnerability Management** | SBOM auto-gen, CVE correlation, reachability analysis (90% noise reduction) |
| **Cloud Security Posture** | S3 public access, IAM over-permissive, exposed SGs, CIS/NIST/SOC2 |
| **Performance-Security Correlation** | DDoS, cryptojacking, data exfiltration, credential stuffing detection |

---

## 12. Layer 10 — Continuous Learning

**Stores incident outcomes and feeds feedback loop to improve future recommendations.**

### Components

| Component | Description |
|-----------|-------------|
| **Feedback Loop Processor** | Evaluates remediation outcomes, writes learning records to KB |
| **Incident Knowledge Base** | Root causes, playbooks, resolution timelines (ClickHouse + MinIO) |
| **Recommendation Engine** | Surfaces historically successful actions for new incidents |
| **Pattern Mining Engine** | Mines recurring patterns to improve detection thresholds |

### Learning Loop

```
Incident → Resolution → Outcome Evaluation → Knowledge Base → Future Recommendations
```

---

## 13. Layer 11 — NexusUX

**Role-adaptive interface with 5 persona modes.**

| Mode | Persona | Focus |
|------|---------|-------|
| **AI-First** | Noobs, PMs, Execs | Chat interface → natural language answers |
| **SRE** | SREs, Platform Eng | Active problems, evidence chain, topology, AutoHeal queue |
| **Developer** | Backend/Frontend Dev | Service view, trace waterfall, flame graphs, git blame |
| **Executive** | VP Eng, CTO, CFO | SLO compliance, revenue at risk, cost trends, MTTR |
| **Security** | Security Eng, CISO | Runtime security events, CVE matrix, CSPM score |

---

## 14. Configuration Drift Engine

**Cross-cutting concern that detects and remediates drift across all layers.**

### Drift Sources & Remediation

| Drift Source | Detection | Remediation Tool |
|--------------|-----------|------------------|
| K8s config changes | K8s Watch API + Git diff | ArgoCD (self-heal) |
| OS config changes | Ansible fact gathering | Ansible EDA (playbook) |
| Cloud infrastructure | Terraform state diff | Terraform (state apply) |
| Git repo changes | Webhook + branch protection | Auto-revert commit |
| CI/CD pipeline changes | Pipeline audit logs | Git rollback |

### Safety Guardrails

- OPA policy evaluation before any remediation
- Approval workflow for high-impact Terraform actions
- Full audit trail of all drift detections and fixes
- Blast radius calculation before auto-remediation

---

## 15. Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Layer 1 (Sources)** | AWS, Azure, GCP, K8s, OTel SDKs, LLM APIs |
| **Layer 2 (Collection)** | eBPF (libbpf+CO-RE), Go agent, Protocol Buffers |
| **Layer 3 (Ingest)** | Apache Kafka, Apache Flink, Presidio |
| **Layer 4 (Storage)** | Apache Arrow, ClickHouse, Apache Parquet, Apache Iceberg, Apache Kuzu |
| **Layer 5 (Topology)** | Apache Kuzu, Redis, Flink |
| **Layer 6 (AI)** | PyTorch Geometric (GNN), Prophet, LSTM, Merlion, Scikit-Learn |
| **Layer 7 (Remediation)** | OPA Rego, Go, Python |
| **Layer 8 (Simulation)** | SimPy, Redis, Optuna |
| **Layer 9 (Security)** | eBPF LSM hooks, Grype, Syft, Checkov |
| **Layer 10 (Learning)** | Python, ClickHouse, MinIO, Scikit-Learn, PyTorch |
| **Layer 11 (UX)** | React 19, TypeScript, Vite, TailwindCSS, Sigma.js + Graphology, Recharts, D3.js, FastAPI |
| **Drift (Cross-Cutting)** | ArgoCD, Ansible EDA, Terraform |

---

## 16. KPI Benchmarks

| KPI | Target | Beats |
|-----|--------|-------|
| Agent CPU overhead | < 0.5% | Dynatrace (~1-3%) |
| Topology update latency | < 500ms | Dynatrace (~30s) |
| Root cause accuracy | > 85% | Davis AI (~80-85%) |
| Mean time to root cause | < 5 min | Industry avg: 30-60 min |
| Problem noise reduction | > 95% | Dynatrace (~95%) |
| SimulaX accuracy | > 80% | No competitor |
| Auto-remediation MTTR | < 3 min | No competitor |
| Time-to-value | < 30 min | Dynatrace: days |
| Cost vs Dynatrace | > 40% lower TCO | Dynatrace pricing |

---

## 17. Competitor Gap Registry

| Gap ID | Problem | Solution |
|--------|---------|----------|
| G1 | Agent overhead | eBPF-native (<0.5% CPU) |
| G2 | Expensive pricing | Signal-volume pricing with caps |
| G3 | Opaque AI | Full evidence chain + confidence score |
| G4 | Pre-defined playbooks only | Novel strategy generation via LLM+KB |
| G5 | No simulation | SimulaX Digital Twin |
| G6 | Vendor lock-in | NQL = OTel superset, full export |
| G7 | UI complexity | 5 role-adaptive modes |
| G8 | Fixed LLM | BYOM (any OpenAI-compatible model) |
| G9 | No eBPF | GhostCollector is eBPF-first |
| G10 | Closed ecosystem | OpenAgent API, OTLP-native |
| G11 | No causal AI (OSS) | GNN + Granger + Graph traversal |
| G12 | Fragmented storage (OSS) | NexusStore unified lakehouse |
| G13 | No topology (Grafana/OTel) | TopoBrain 8-layer CKG |
| G14 | No self-hosted (Datadog) | Full self-hosted parity |
| G15 | LLM correlation = AI (Datadog) | Hard boundary: causal is deterministic |
| G16 | No GenAI observability | Native LLM call tracing + cost |
| G17 | No business mapping | BusinessLens revenue impact |
| G18 | No BubbleUp (Honeycomb) | DiffEngine cross-signal |
| G19 | No cost/carbon | CostBrain per-entity tracking |
| G20 | No pre-fix simulation | SimulaX shadow-mode |

---

*Document Version: 2.0 | Generated: July 2026 | Classification: Internal R&D*
