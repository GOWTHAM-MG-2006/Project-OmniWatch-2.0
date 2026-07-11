# OmniWatch 2.0

**AI-Driven Cloud Operations (AIOps) Platform**

> Proactive anomaly detection, causal root cause analysis, autonomous remediation, digital twin simulation, and self-healing for cloud-native environments.

---

## Architecture

OmniWatch 2.0 implements an **11-layer architecture** with a cross-cutting Configuration Drift Engine:

```
Layer 1:  DATA SOURCES (K8s │ VMs │ Cloud │ Browsers │ LLM APIs │ Databases)
              │
Layer 2:  GHOSTCOLLECTOR (eBPF Kernel │ Bytecode │ OTLP │ Cloud API │ RUM │ LLM)
              │
Layer 3:  STREAMFORGE (Entity Resolution │ Windowing │ Tail Sampling │ PII)
              │
Layer 4:  NEXUSSTORE (Hot: Arrow │ Warm: ClickHouse │ Cold: Parquet/Iceberg │ Graph: Kuzu)
              │
Layer 5:  TOPOBRAIN (8-Layer Causal Knowledge Graph │ <500ms Updates)
              │
Layer 6:  NEUROENGINE (Causal │ Predictive │ Generative │ DiffEngine)
              │
Layer 7:  AUTOHEAL (OPA Policy │ 5 Autonomy Tiers │ Config Drift → ArgoCD/Ansible/Terraform)
              │
Layer 8:  SIMULAX (Digital Twin │ What-If Simulation │ Shadow Validation)
              │
Layer 9:  SENTINELPLANE (Runtime Security │ CVE │ CSPM)
              │
Layer 10: CONTINUOUS LEARNING (Feedback Loop │ Pattern Mining │ Recommendations)
              │
Layer 11: NEXUSUX (AI-First │ SRE │ Developer │ Executive │ Security)
```

---

## Phase 7: Ecosystem & Scale

Phase 7 expands OmniWatch with ecosystem breadth and business intelligence:

### Integration Library (25+ Integrations)
- **Cloud**: AWS EC2/EKS/RDS/Lambda, Azure VMs/AKS, GCP GKE/Compute
- **Database**: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch
- **Message Queue**: RabbitMQ, NATS, Pulsar
- **Web Server**: Nginx, Apache
- **CI/CD**: Jenkins, CircleCI
- **Monitoring**: Prometheus Export, Grafana Dashboard, Jaeger Export
- **Security**: Wazuh SIEM, Suricata IDS

### Pricing Engine
- Usage-based pricing with 4 tiers (Free, Starter, Pro, Enterprise)
- Real-time cost tracking and projections
- Cost optimization recommendations

### Business Intelligence
- **BusinessLens**: Maps IT anomalies to business transactions and revenue impact
- **CostBrain**: Real-time cloud cost and carbon footprint tracking per entity

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/omniwatch-2.0.git
cd omniwatch-2.0

# Start all infrastructure
docker-compose up -d

# Access the dashboard
open http://localhost:3000
```

### Service Endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| Dashboard Frontend | http://localhost:3000 | — |
| Dashboard Backend | http://localhost:8000 | — |
| MinIO Console | http://localhost:9002 | minioadmin / minioadmin |
| ClickHouse | localhost:9000 | default / (no password) |
| Kafka | localhost:9092 | — |
| OPA | http://localhost:8181 | — |
| Ollama API | http://localhost:11434 | — |

---

## Technology Stack

| Category | Technologies |
|----------|-------------|
| **Collection** | eBPF (libbpf+CO-RE), Go, Rust, Protocol Buffers |
| **Stream Processing** | Apache Kafka, Apache Flink |
| **Storage** | Apache Arrow, ClickHouse, Apache Parquet, Apache Iceberg, Apache Kuzu, MinIO |
| **AI/ML** | PyTorch Geometric (GNN), Prophet, LSTM, Scikit-Learn, Optuna |
| **GenAI** | vLLM, LiteLLM, Qwen, Llama 3 (BYOM) |
| **Policy** | Open Policy Agent (OPA) Rego |
| **Security** | eBPF LSM hooks, Grype, Syft, Checkov |
| **Config Drift** | ArgoCD, Ansible EDA, Terraform |
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS, Sigma.js, Recharts, D3.js |
| **Backend** | FastAPI, Python 3.11+ |
| **Infrastructure** | Kubernetes, Docker, Helm, ArgoCD (GitOps) |

---

## Project Structure

```
├── ingestion/              # Layer 2+3: GhostCollector + StreamForge
├── storage/                # Layer 4: NexusStore (4-tier data lakehouse)
├── topology/               # Layer 5: TopoBrain (8-layer causal knowledge graph)
├── ai/                     # Layer 6: NeuroEngine (4-mode AI)
│   ├── causal/             #   Causal detection (GNN + Granger)
│   ├── predictive/         #   Predictive forecasting (Prophet + LSTM)
│   ├── generative/         #   Generative AI (BYOM + grounding)
│   ├── diff_engine/        #   Differential analysis (BubbleUp extended)
│   └── business/           #   Business intelligence (BusinessLens + CostBrain)
├── remediation/            # Layer 7: AutoHeal + Config Drift
│   ├── auto_heal/          #   Autonomous remediation (OPA + 5 tiers)
│   ├── config_drift/       #   Drift detection + ArgoCD/Ansible/Terraform
│   └── policies/           #   OPA Rego policies
├── simulation_engine/      # Layer 8: SimulaX (Digital Twin + 4 sim modes)
├── security/               # Layer 9: SentinelPlane (Runtime + CVE + CSPM)
├── learning/               # Layer 10: Continuous Learning (KB + patterns)
├── dashboard/              # Layer 11: NexusUX (FastAPI + React)
├── integrations/           # 25+ integration connectors
│   ├── library/            #   Cloud, DB, MQ, Web, CI/CD, Monitoring, Security
│   ├── base.py             #   BaseIntegration abstract class
│   └── registry.py         #   Integration registry
├── billing/                # Pricing engine
│   ├── pricing_engine.py   #   Usage-based pricing calculation
│   └── pricing_dashboard.py #  FastAPI billing API
├── k8s/                    # Kubernetes manifests
├── docs/                   # Architecture & design documents
└── docker-compose.yml      # Full local infrastructure stack
```

---

## Key Features

- **eBPF-native collection** — Zero-code, <0.5% CPU overhead
- **8-layer causal knowledge graph** — TopoBrain with <500ms updates
- **4-mode NeuroEngine** — Causal + Predictive + Generative + DiffEngine
- **SimulaX Digital Twin** — Simulate before you remediate
- **5-tier autonomous remediation** — From observe-only to predictive autonomous
- **Configuration drift engine** — Auto-remediate K8s, OS, Cloud, Git drift
- **LLM observability** — Track model, tokens, latency, cost per call
- **Continuous learning** — Feedback loop improves future decisions
- **Role-adaptive UI** — 5 persona modes (AI-First, SRE, Developer, Executive, Security)

---

## Documentation

| Document | Description |
|----------|-------------|
| `AGENTS.md` | Architecture, data contracts, coding standards |
| `docs/New-System-Architecture.md` | Complete 11-layer architecture specification |
| `docs/DataFlow.md` | End-to-end data flow diagrams |
| `docs/Build-Plan.md` | 4-phase, 24-month implementation roadmap |
| `docs/Competitor-Analysis.md` | Dynatrace deep-dive comparison |
| `docs/Open-Source-Comparison.md` | OSS vs Dynatrace analysis |

---

## Data Contracts

All inter-component communication uses well-defined JSON schemas:

- **AnomalySignal** — StreamForge → NeuroEngine
- **RootCauseObject** — NeuroEngine → AutoHeal
- **IncidentRecord** — NeuroEngine → AutoHeal
- **SimulaXResult** — SimulaX → AutoHeal
- **ActionResult** — AutoHeal → Learning
- **ConfigDriftEvent** — Config Drift → AutoHeal
- **SecurityAnomalySignal** — SentinelPlane → NeuroEngine

See `AGENTS.md` for complete schema definitions.

---

## Competition

| Field | Value |
|-------|-------|
| **Competition** | IEEE YESIST12 2026 — IEngage Track |
| **Problem** | Proactive Anomaly Detection Intelligence |
| **Approach** | Fully open-source, zero vendor lock-in, locally runnable |
| **Cost** | $0 (all open-source stack) |

---

## License

Internal R&D — IEEE YESIST12 2026 Competition Entry

---

*OmniWatch 2.0 | Version 4.0 | July 2026 | All 7 Phases Complete*
