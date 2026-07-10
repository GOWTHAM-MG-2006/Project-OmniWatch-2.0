# OmniWatch 2.0 — Complete Data Flow Specification

---

## 1. End-to-End Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: DATA SOURCES                                                      │
│  K8s Pods | VMs | Bare Metal | Serverless | Browsers | LLM APIs            │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ Raw Telemetry
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: GHOSTCOLLECTOR (eBPF-Native Collection)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ eBPF Kernel │ │ Bytecode    │ │ OTLP     │ │ Cloud    │ │ RUM +    │  │
│  │ Probes      │ │ Injection   │ │ Receiver │ │ API Poll │ │ LLM      │  │
│  └──────┬──────┘ └──────┬──────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│         └───────────────┴─────────────┴────────────┴────────────┘        │
│                                    │ Unified OTLP Signal                   │
└────────────────────────────────────┼───────────────────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: STREAMFORGE (Intelligent Ingest Pipeline)                        │
│                                                                             │
│  Stage 1: Receipt & Validation                                             │
│    → Multi-protocol: OTLP, PromQL, Loki, ES Bulk, Kafka                   │
│    → Schema validation, mTLS auth, rate limiting                           │
│                                    │                                        │
│                                    ▼                                        │
│  Stage 2: Enrichment Engine                                                │
│    → Semantic Dictionary (field normalization)                             │
│    → Entity Resolution (volatile IDs → stable entities)                    │
│    → Cost enrichment (per-request cloud cost estimate)                     │
│    → Carbon enrichment (kg CO₂ per compute unit)                          │
│    → Geo-enrichment (IP → lat/lon, ASN)                                   │
│    → SLO context tagging                                                   │
│                                    │                                        │
│                                    ▼                                        │
│  Stage 3: Adaptive Intelligence                                            │
│    → Tail-Based Causal Sampling (keep errors, drop normal)                 │
│    → Anomaly-Prioritized Routing (anomalous → hot, normal → cold)          │
│    → Privacy-by-Default PII Engine (regex + ML detection)                  │
│                                    │                                        │
│                                    ▼                                        │
│  Stage 4: Windowing Layer (Flink)                                          │
│    → Time windowing (5s → 1-min aggregates)                               │
│    → Time alignment (all signals share same timestamps)                    │
│    → Feature engineering (rolling mean, z-score, error ratio)              │
│    → Missing data handling (interpolation, forward-fill)                   │
│    → ML-ready feature vectors                                              │
│                                    │                                        │
│                                    ▼                                        │
│  Stage 5: Topology Delta Publisher                                         │
│    → Publishes topology edges to TopoBrain (<500ms)                        │
│                                    │                                        │
│                                    ▼                                        │
│  Stage 6: Multi-Destination Routing                                        │
│    ├─→ NexusStore (primary)                                                │
│    ├─→ S3/GCS (mirror)                                                     │
│    ├─→ External OTLP (forward)                                             │
│    └─→ Parquet archive (cold)                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                    ┌────────────────┴─────────────────┐
                    ▼                                  ▼
┌──────────────────┐ ┌──────────────────┐
│  LAYER 4:        │ │  LAYER 5:        │
│  NEXUSSTORE      │ │  TOPOBRAIN       │
│  (Storage)       │ │  (Topology)      │
│                  │ │                  │
│  Hot: Arrow      │ │  8-Layer CKG     │
│  Warm: ClickHouse│ │  <500ms updates  │
│  Cold: Parquet   │ │  Entity graph    │
│  Graph: Kuzu     │ │                  │
└────────┬─────────┘ └────────┬─────────┘
         │                    │
         └────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 6: NEUROENGINE (Hypermodal AI)                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  MODE 1: CAUSAL DETECTION ENGINE (Deterministic)                    │   │
│  │  → Dynamic Baseline (Holt-Winters + ARIMA)                         │   │
│  │  → Multi-Signal Anomaly Detection (Metrics+Logs+Traces+Topology)   │   │
│  │  → Causal Graph Traversal (Granger + GNN + DAG Walker)             │   │
│  │  → Problem Assembly (group anomalies → ONE Problem)                 │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                            │
│  ┌─────────────────────────────▼───────────────────────────────────────┐   │
│  │  MODE 2: PREDICTIVE ENGINE (ML Forecasting)                         │   │
│  │  → Prophet + LSTM → Disk/Memory/CPU exhaustion forecasts            │   │
│  │  → Auto-triggers AutoHeal for predictive issues                     │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                            │
│  ┌─────────────────────────────▼───────────────────────────────────────┐   │
│  │  MODE 3: GENERATIVE AI (BYOM — GPT/Claude/Gemini/Llama)            │   │
│  │  → NL Query, Summary, Postmortem, Code Fix, Dashboard Gen           │   │
│  │  → Grounding Guardrail (evidence-backed only)                       │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                            │
│  ┌─────────────────────────────▼───────────────────────────────────────┐   │
│  │  MODE 4: DIFFERENTIAL ANALYSIS (DiffEngine)                         │   │
│  │  → Cross-signal BubbleUp → ranked causal hypotheses                 │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │ Root Cause Object + Evidence Chain         │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 7: AUTOHEAL (Autonomous Remediation)                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  OPA Policy Engine                                                  │   │
│  │  → IF confidence > 95% AND severity = P1 → Auto-Remediate           │   │
│  │  → IF medium confidence → Approval Workflow → Human sign-off        │   │
│  │  → IF Tier 3+ → SimulaX Validation Gate → Execute if pass           │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                            │
│  ┌─────────────────────────────▼───────────────────────────────────────┐   │
│  │  Action Library                                                     │   │
│  │  → restart pod, rollback, scale, rotate credentials                 │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                            │
│  ┌─────────────────────────────▼───────────────────────────────────────┐   │
│  │  Auto Remediation Engine                                            │   │
│  │  → K8s API (kubectl)                                                │   │
│  │  → AWS/Azure/GCP APIs                                               │   │
│  │  → Scripts + Rollback auto-generated                                │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                            │
│  ┌─────────────────────────────▼───────────────────────────────────────┐   │
│  │  Configuration Drift Engine                                         │   │
│  │  → K8s Drift → ArgoCD self-heal                                     │   │
│  │  → OS Drift → Ansible EDA playbook                                  │   │
│  │  → Cloud Drift → Terraform state apply                              │   │
│  │  → Git Drift → Auto-revert commit                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Output: Remediation Executed + Rollback Plan + Audit Log                  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                    ┌────────────────┴─────────────────┐
                    ▼                                  ▼
┌──────────────────┐ ┌──────────────────┐
│  LAYER 8:        │ │  LAYER 9:        │
│  SIMULAX         │ │  SENTINELPLANE   │
│  (Digital Twin)  │ │  (Security)      │
│                  │ │                  │
│  Shadow sim      │ │  Runtime security│
│  before execute  │ │  CVE reachability│
│                  │ │  CSPM compliance │
└──────────────────┘ └────────┬─────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 10: INCIDENT KNOWLEDGE BASE & CONTINUOUS LEARNING                   │
│                                                                             │
│  Feedback Loop Processor                                                    │
│    → Evaluates remediation outcomes                                         │
│    → Writes learning records to KB                                          │
│                                                                             │
│  Incident Knowledge Base                                                    │
│    → Root causes, playbooks, resolution timelines                           │
│                                                                             │
│  Recommendation Engine                                                     │
│    → Surfaces historically successful actions                               │
│                                                                             │
│  Pattern Mining Engine                                                     │
│    → Mines recurring patterns → updates detection thresholds               │
│    → Feeds back to NeuroEngine Adaptive Thresholder                         │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 11: NEXUSUX (Role-Adaptive Experience)                              │
│                                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ AI-First     │ │ SRE Mode     │ │ Developer    │ │ Executive    │      │
│  │ Chat → NQL   │ │ Problems,    │ │ Traces,      │ │ SLO, Cost,   │      │
│  │ + English    │ │ Evidence,    │ │ Flame graphs,│ │ Revenue,     │      │
│  │              │ │ Topology     │ │ Git blame    │ │ MTTR         │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
│                                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                       │
│  │ Security     │ │ Incident     │ │ Knowledge    │                       │
│  │ Mode         │ │ Explorer     │ │ Base Explorer│                       │
│  │ CVE, CSPM,   │ │ Root cause   │ │ Historical   │                       │
│  │ MITRE ATT&CK │ │ timeline     │ │ incidents    │                       │
│  └──────────────┘ └──────────────┘ └──────────────┘                       │
│                                                                             │
│  API Gateway (FastAPI) → React Frontend                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer-by-Layer Data Flow

### Flow 1: Telemetry Ingestion (Layer 1 → Layer 2)

```
Cloud Services (AWS/Azure/GCP)  →  OTel Collector  →  Kafka
Kubernetes Pods                 →  OTel Collector  →  Kafka
Security Systems                →  OTel Collector  →  Kafka
Applications                    →  OTel Collector  →  Kafka
Browser/Mobile                  →  RUM Agent       →  Kafka
LLM APIs                        →  Framework Hooks →  Kafka
```

### Flow 2: Stream Processing (Layer 3)

```
Kafka → Flink (normalize + enrich + correlate)
  → Entity Resolution (stabilize IDs)
  → Windowing (align + aggregate + feature engineering)
  → ClickHouse (warm storage)
  → Kuzu (graph storage)
  → MinIO/S3 (cold archive)
  → TopoBrain (topology deltas)
```

### Flow 3: Anomaly Detection (Layer 6 — Mode 1)

```
ClickHouse (windowed features)
  → Merlion (anomaly detection)
  → Adaptive Thresholder (dynamic baselines)
  → Noise Reduction Filter (suppress spikes)
  → Anomaly Scorer (normalized score + confidence)
  → Signal Enrichment Engine (join with topology + SLA)
  → Enriched Anomaly Object
```

### Flow 4: Root Cause Analysis (Layer 6 — Mode 1)

```
Enriched Anomaly Object
  → Incident Aggregation Layer (group related alerts)
  → Incident Prioritization Engine (P1-P4 + Business Impact Score)
  → Causal Graph Intelligence Engine
    → Dependency Discovery (auto-discover relationships)
    → Cross-Cloud Dependency Mapper (AWS ↔ Azure ↔ GCP)
    → DAG Traversal Engine (backward BFS)
    → Root Cause Object Builder (entity + confidence + path)
  → Root Cause Object with Evidence Chain
```

### Flow 5: Remediation Execution (Layer 7)

```
Root Cause Object
  → OPA Policy Engine (Rego evaluation)
  → High confidence → Action Library → Auto Remediation Engine
  → Medium confidence → Approval Workflow → Human → Execute
  → Tier 3+ → SimulaX Shadow Simulation → Execute if pass
  → K8s/AWS/Azure/GCP APIs → Action Executed
  → Rollback Plan auto-generated
  → Full Audit Log
```

### Flow 6: Configuration Drift Resolution (Cross-Cutting)

```
Drift Detection
  → Git diff / K8s Watch / Terraform plan
  → Drift classified by layer:
    K8s → ArgoCD (self-heal sync)
    OS → Ansible EDA (rulebook + playbook)
    Cloud → Terraform (state reconciliation)
    Git → Auto-revert commit
  → Approval gate for high-impact actions
  → Resolution executed
  → Audit logged
```

### Flow 7: Generative AI Reports (Layer 6 — Mode 3)

```
Root Cause Object + Incident Context + Historical Incidents
  → vLLM Inference Server (Qwen/Llama or BYOM)
  → 4 Generators:
    → Incident Summary Generator (for engineers)
    → Executive Report Generator (for stakeholders)
    → Runbook Generator (step-by-step fix)
    → Post-Incident Analyser (post-mortem)
  → Dashboard (delivered via API Gateway)
```

### Flow 8: Continuous Learning (Layer 10)

```
Remediation Outcome
  → Feedback Loop Processor (evaluate success)
  → Incident Knowledge Base (store root cause, resolution, success rate)
  → Recommendation Engine (surface historically successful actions)
  → Pattern Mining Engine (mine recurring patterns)
  → Update detection thresholds (feed back to NeuroEngine)
  → Update Action Library (inject historically successful actions)
```

---

## 3. JSON Object Formats

### Anomaly Object (from Layer 3 StreamForge)

```json
{
  "entity": "payment-service",
  "entity_type": "SERVICE",
  "score": 0.96,
  "confidence": 95,
  "metric": "p99_latency",
  "deviation": "890ms vs baseline 45ms",
  "timestamp": "2026-07-03T08:14:32Z",
  "topology_context": {
    "layer": 5,
    "depends_on": ["postgres-payments-primary", "redis-cache"],
    "depended_by": ["checkout-service", "order-service"]
  }
}
```

### Incident Record (from Layer 6 Prioritization)

```json
{
  "incident_id": "INC-2026-07-001",
  "severity": "P1",
  "impact_score": 97,
  "root_cause_entity": "postgres-payments-primary",
  "affected_services": ["payment-service", "checkout-service", "frontend"],
  "total_anomalies_grouped": 6,
  "propagation_path": "DB → Payment → Checkout → Frontend",
  "started_at": "2026-07-03T08:12:11Z",
  "sla_breach": true
}
```

### Root Cause Object (from Layer 6 Causal Engine)

```json
{
  "root_cause": "Storage Node",
  "entity": "postgres-payments-primary",
  "confidence": 98,
  "causal_score": 0.94,
  "evidence_chain": [
    "CPU spike on host payments-db-02 preceded DB latency by 2s",
    "Granger causality: host CPU → DB latency (p=0.0003)",
    "Deployment event: payments-analytics v2.1.4 deployed to same host"
  ],
  "dependency_path": "Frontend → Checkout → Payment → DB → Host",
  "impacted_services": ["payment-service", "checkout-service", "frontend"]
}
```

### SimulaX Result Object (from Layer 8)

```json
{
  "simulation_id": "SIM-20260703-00481",
  "mode": "REMEDIATION_SIMULATION",
  "proposed_action": {
    "type": "ROLLBACK",
    "target": "payments-analytics",
    "from_version": "v2.1.4",
    "to_version": "v2.1.3"
  },
  "predicted_outcome": {
    "resolution_confidence": 0.91,
    "recovery_time_minutes": 8,
    "side_effects": ["payments-reporting unavailable (v2.1.4 only feature)"],
    "revenue_recovery_usd": 84200
  },
  "risk_score": 0.12,
  "recommendation": "PROCEED"
}
```

---

## 4. Structural Validation

```
Layer 1:  Data Sources
  ↓
Layer 2:  GhostCollector (eBPF Collection)
  ↓
Layer 3:  StreamForge (Entity Resolution + Windowing)
  ↓
Layer 4:  NexusStore (ClickHouse + Kuzu + MinIO)
  ↓
Layer 5:  TopoBrain (8-Layer Graph)
  ↓
Layer 6:  NeuroEngine (Anomaly Detection + Causal Inference)
  ↓
Layer 7:  AutoHeal (Policy Evaluation → Remediation Execution)
  ↓
Layer 8:  SimulaX (Shadow Simulation Validation)
  ↓
Layer 9:  SentinelPlane (Security Check)
  ↓
Layer 10: Continuous Learning (Feedback → Pattern Mining → Recommendations)
  ↓
Layer 11: NexusUX (Dashboard)
```

**No circular dependency errors. Logically consistent.**

---

*Document Version: 2.0 | Generated: July 2026*
