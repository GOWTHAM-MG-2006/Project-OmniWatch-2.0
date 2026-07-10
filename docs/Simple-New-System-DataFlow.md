# OmniWatch 2.0 — Simple Data Flow & System Design

## ASCII Architecture Overview

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          OMNIWATCH 2.0 — FULL STACK                           ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │                   LAYER 11: NEXUSUX (Dashboard)                        │  ║
║  │   AI-First Chat │ SRE Mode │ Dev Mode │ Executive │ Security │ Mobile  │  ║
║  └───────────────────────────────────┬─────────────────────────────────────┘  ║
║                                      │                                        ║
║  ┌───────────────┐ ┌───────────────┐ │ ┌───────────────┐ ┌───────────────┐   ║
║  │  LAYER 8      │ │  LAYER 9      │ │ │  LAYER 7      │ │  LAYER 6      │   ║
║  │  SIMULAX      │ │  SENTINEL     │ │ │  AUTOHEAL     │ │  NEUROENGINE  │   ║
║  │               │ │  PLANE        │ │ │               │ │               │   ║
║  │  Digital Twin │ │  Security     │ │ │  Auto-Remedy  │ │  Causal AI    │   ║
║  │  What-If Sim  │ │  CVE + CSPM   │ │ │  + Config     │ │  Predictive   │   ║
║  │               │ │               │ │ │    Drift      │ │  + Generative │   ║
║  └───────┬───────┘ └───────┬───────┘ │ └───────┬───────┘ └───────┬───────┘   ║
║          │                 │         │         │                 │            ║
║  ┌───────▼─────────────────▼─────────▼─────────▼─────────────────▼─────────┐ ║
║  │                    LAYER 5: TOPOBRAIN (8-Layer Graph)                   │ ║
║  │  Cost │ Infra │ Hosts │ Processes │ Services │ Apps │ GenAI │ Business  │ ║
║  └───────────────────────────────────┬─────────────────────────────────────┘ ║
║                                      │                                       ║
║  ┌───────────────────────────────────▼─────────────────────────────────────┐ ║
║  │                    LAYER 4: NEXUSSTORE (4-Tier Storage)                 │ ║
║  │   Hot: Arrow │ Warm: ClickHouse │ Cold: Parquet │ Graph: Kuzu           │ ║
║  └───────────────────────────────────┬─────────────────────────────────────┘ ║
║                                      │                                       ║
║  ┌───────────────────────────────────▼─────────────────────────────────────┐ ║
║  │                    LAYER 3: STREAMFORGE (Ingest Pipeline)               │ ║
║  │  Entity Resolution │ Windowing │ Tail Sampling │ PII Engine             │ ║
║  └───────────────────────────────────┬─────────────────────────────────────┘ ║
║                                      │                                       ║
║  ┌───────────────────────────────────▼─────────────────────────────────────┐ ║
║  │                  LAYER 2: GHOSTCOLLECTOR (eBPF Collection)              │ ║
║  │  eBPF Kernel │ Bytecode │ OTLP │ Cloud API │ RUM │ LLM Observability   │ ║
║  └───────────────────────────────────┬─────────────────────────────────────┘ ║
║                                      ↑                                       ║
║  ┌───────────────────────────────────▼─────────────────────────────────────┐ ║
║  │                    LAYER 1: DATA SOURCES                                │ ║
║  │   K8s │ VMs │ Bare Metal │ Serverless │ Browsers │ LLM APIs │ Databases│ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │               LAYER 10: CONTINUOUS LEARNING & KNOWLEDGE BASE           │  ║
║  │   Feedback Loop │ Pattern Mining │ Recommendations │ Knowledge Base     │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Simple Data Flow

```
                    ┌─────────────────────────────────┐
                    │   LAYER 1: DATA SOURCES         │
                    │  K8s │ VMs │ Cloud │ Browsers   │
                    └──────────────┬──────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────┐
                    │  LAYER 2: GHOSTCOLLECTOR (eBPF) │
                    │  6 Collection Modes              │
                    │  Zero code change, <0.5% CPU    │
                    └──────────────┬──────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────┐
                    │  LAYER 3: STREAMFORGE            │
                    │  Entity Resolution               │
                    │  Windowing (Flink)               │
                    │  Tail Sampling                   │
                    │  PII Engine                      │
                    └──────┬────────────┬─────────────┘
                           │            │
                           ▼            ▼
              ┌────────────────┐  ┌────────────────┐
              │  LAYER 4:      │  │  LAYER 5:      │
              │  NEXUSSTORE    │  │  TOPOBRAIN     │
              │  ClickHouse    │  │  8-Layer Graph  │
              │  Kuzu           │  │  <500ms update  │
              │  MinIO/Parquet │  │                │
              └───────┬────────┘  └───────┬────────┘
                      │                   │
                      └─────────┬─────────┘
                                ▼
                    ┌─────────────────────────────────┐
                    │  LAYER 6: NEUROENGINE (AI)      │
                    │  Causal Detection (GNN+Granger) │
                    │  Predictive (Prophet+LSTM)      │
                    │  Generative (BYOM)              │
                    │  DiffEngine (BubbleUp)          │
                    └──────────────┬──────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────┐
                    │  LAYER 7: AUTOHEAL (Remediation) │
                    │  OPA Policy Engine               │
                    │  5 Autonomy Tiers                │
                    │  Config Drift → ArgoCD/Ansible/  │
                    │                Terraform         │
                    └──────┬────────────┬──────────────┘
                           │            │
                           ▼            ▼
              ┌────────────────┐  ┌─────────────────┐
              │  LAYER 8:      │  │  LAYER 9:       │
              │  SIMULAX       │  │  SENTINELPLANE  │
              │  Digital Twin  │  │  Security       │
              │  Shadow Sim    │  │  CVE + CSPM     │
              └────────────────┘  └─────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────┐
                    │  LAYER 10: CONTINUOUS LEARNING   │
                    │  Pattern Mining → Thresholds     │
                    │  Recommendations → Actions       │
                    └──────────────┬───────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────┐
                    │  LAYER 11: NEXUSUX (Dashboard)   │
                    │  AI-First │ SRE │ Dev │ Exec     │
                    └──────────────────────────────────┘
```

---

## 11-Layer Stack (Bottom to Top)

```
┌─────────────────────────────────────────────────────────┐
│  11. NEXUSUX          │ React + FastAPI + Sigma.js      │
├─────────────────────────────────────────────────────────┤
│  10. CONTINUOUS       │ Pattern Mining + KB +           │
│      LEARNING         │ Recommendations                 │
├─────────────────────────────────────────────────────────┤
│   9. SENTINELPLANE    │ eBPF Security + CVE + CSPM     │
├─────────────────────────────────────────────────────────┤
│   8. SIMULAX          │ Digital Twin + 4 Sim Modes      │
├─────────────────────────────────────────────────────────┤
│   7. AUTOHEAL         │ OPA + 5 Tiers + Config Drift    │
├─────────────────────────────────────────────────────────┤
│   6. NEUROENGINE      │ Causal + Predictive + GenAI     │
│                       │ + DiffEngine + BYOM             │
├─────────────────────────────────────────────────────────┤
│   5. TOPOBRAIN        │ 8-Layer Graph + <500ms Updates  │
├─────────────────────────────────────────────────────────┤
│   4. NEXUSSTORE       │ Hot/Warm/Cold/Graph + NQL       │
├─────────────────────────────────────────────────────────┤
│   3. STREAMFORGE      │ Entity Resolution + Windowing   │
│                       │ + Tail Sampling + PII           │
├─────────────────────────────────────────────────────────┤
│   2. GHOSTCOLLECTOR   │ eBPF + Bytecode + OTLP +       │
│                       │ Cloud API + RUM + LLM           │
├─────────────────────────────────────────────────────────┤
│   1. DATA SOURCES     │ K8s │ VMs │ Cloud │ Browsers    │
│                       │ │ LLM APIs │ Databases          │
└─────────────────────────────────────────────────────────┘
```

---

## Key Differentiators vs Dynatrace

```
┌────────────────────────────────────────────────────────────────────┐
│  FEATURE                    │ DYNATRACE      │ OMNIWATCH 2.0       │
├────────────────────────────────────────────────────────────────────┤
│  Collection Method          │ Process inject │ eBPF-native         │
│  CPU Overhead               │ ~1-3%          │ < 0.5%             │
│  Topology Layers            │ 5 tiers        │ 8 layers           │
│  Topology Update            │ ~30s batch     │ <500ms real-time   │
│  AI Root Cause              │ Opaque         │ Full evidence chain │
│  AI Confidence Score        │ Binary         │ 0.0-1.0 continuous │
│  Digital Twin / Simulation  │ None           │ 4 simulation modes │
│  Self-Hosted Option         │ None           │ Full parity        │
│  GenAI Workload Observability│ None          │ Native LLM tracking│
│  Cost/Carbon per Entity     │ None           │ Native tracking    │
│  Config Drift Resolution    │ Indicates only │ Auto-remediates    │
│  BYOM (Any LLM)            │ Fixed LLM      │ Any model          │
│  Differential Analysis      │ None           │ DiffEngine         │
│  Vendor Lock-In             │ High (DQL)     │ None (OTel/NQL)    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Complete Lifecycle Example

```
AWS Database Latency Spike
        │
        ▼
Layer 2: GhostCollector eBPF captures CPU spike on host
        │
        ▼
Layer 3: StreamForge Entity Resolution stabilizes pod IDs
        │
        ▼
Layer 3: StreamForge Windowing aligns metrics into feature vectors
        │
        ▼
Layer 4: ClickHouse stores windowed data
        │
        ▼
Layer 6: Merlion detects anomaly (CPU 12% → 94%)
        │
        ▼
Layer 6: Incident Aggregation groups 6 related alerts → 1 incident
        │
        ▼
Layer 6: Prioritization Engine: P1 Critical, Impact Score 97
        │
        ▼
Layer 5: TopoBrain DAG Traversal: Frontend → Checkout → Payment → DB → Host
        │
        ▼
Layer 6: Root Cause: "Host payments-db-2 CPU spike (from deployment)"
        │
        ▼
Layer 8: SimulaX shadow-simulate rollback of payments-analytics v2.1.4
        │
        ▼
Layer 8: SimulaX Result: Resolution confidence 91%, recovery in 8 min
        │
        ▼
Layer 7: OPA: Confidence > 95% → Auto-Remediate
        │
        ▼
Layer 7: Auto Remediation: Rollback payments-analytics to v2.1.3
        │
        ▼
Layer 9: SentinelPlane: Security check passed
        │
        ▼
Layer 6: GenAI: Incident summary + runbook generated
        │
        ▼
Layer 11: NexusUX: Dashboard shows resolved, MTTR = 3 min
        │
        ▼
Layer 10: Knowledge Base: Stores outcome for future recommendations
        │
        ▼
Layer 10: Pattern Mining: Updates detection thresholds
        │
        ▼
Future incidents: System is smarter
```

---

*Document Version: 2.0 | Generated: July 2026*
