# OmniWatch 2.0 — Build Plan & Implementation Roadmap

---

## Overview

This document defines the phased implementation plan for OmniWatch 2.0 — a next-generation AIOps platform that combines the New-System.md requirements (11 layers) with the refined system's unique innovations (Entity Resolution, Windowing, Configuration Drift, Incident Aggregation).

**Total Duration:** 24 months (4 phases × 6 months each)

---

## Phase 1: Foundation (Months 1–6)

### Goal
Minimal Viable Platform — better than SigNoz, competitive with New Relic basic tier.

### Deliverables

| # | Component | Layer | Description | Technology |
|---|-----------|-------|-------------|------------|
| 1.1 | **GhostCollector v1.0** | Layer 2 | eBPF HTTP/gRPC/SQL capture + OTLP receiver | eBPF (libbpf+CO-RE), Go, Rust |
| 1.2 | **StreamForge v1.0** | Layer 3 | Kafka + Flink (normalize + enrich + correlate) | Apache Kafka, Apache Flink |
| 1.3 | **Entity Resolution Layer** | Layer 3 | Maps volatile pod/container IDs to stable entities | Flink stateful keyed stream, RocksDB |
| 1.4 | **Windowing Layer** | Layer 3 | Flink tumbling windows + feature engineering | Apache Flink |
| 1.5 | **NexusStore v1.0** | Layer 4 | ClickHouse warm store (logs + metrics + traces) | ClickHouse |
| 1.6 | **TopoBrain v1.0** | Layer 5 | Basic service-level dependency graph from traces | Apache Kuzu |
| 1.7 | **NQL v1.0** | Layer 4 | PromQL + LogQL compatibility + basic cross-signal join | Go |
| 1.8 | **NexusUX v1.0** | Layer 11 | Developer mode + SRE mode dashboards | React, TypeScript, FastAPI |
| 1.9 | **Incident Aggregation** | Layer 6 | Groups related alerts into single incidents | Python |
| 1.10 | **Incident Prioritization** | Layer 6 | P1-P4 severity + Business Impact Score | Python, FastAPI |

### Success Criteria

| KPI | Target |
|-----|--------|
| Ingest throughput | 1TB/day per tenant reliably |
| Query response (warm tier) | < 100ms |
| GhostCollector CPU overhead | < 1% |
| Zero code change | Java + Go + Node.js |
| Time to first topology | < 60s from agent install |

### Tech Stack (Phase 1)

```
Collection:    eBPF (libbpf), Go agent, Protocol Buffers
Processing:    Apache Kafka, Apache Flink
Storage:       ClickHouse (warm), Apache Kuzu (graph)
Frontend:      React 19, TypeScript, FastAPI
Infrastructure: Kubernetes, Docker, Helm
```

---

## Phase 2: Intelligence (Months 7–12)

### Goal
Surpass Dynatrace's causal AI depth.

### Deliverables

| # | Component | Layer | Description | Technology |
|---|-----------|-------|-------------|------------|
| 2.1 | **TopoBrain v2.0** | Layer 5 | Full 8-layer entity model; < 500ms update latency | Kuzu, Flink, Redis |
| 2.2 | **NeuroEngine v2.0 — Causal** | Layer 6 | GNN (CausalGNN) + Granger Causality + graph traversal | PyTorch Geometric, statsmodels |
| 2.3 | **NeuroEngine v2.0 — Explainability** | Layer 6 | Full evidence chain output (JSON) | Python |
| 2.4 | **NeuroEngine v2.0 — Generative** | Layer 6 | LLM integration + BYOM (any OpenAI-compatible model) | vLLM, LiteLLM |
| 2.5 | **NexusStore v2.0** | Layer 4 | Cold tier (Parquet + Iceberg) + continuous profiling | Parquet, Iceberg, DuckDB |
| 2.6 | **StreamForge v2.0** | Layer 3 | Tail-based causal sampling + anomaly-prioritized routing | Flink |
| 2.7 | **StreamForge v2.0** | Layer 3 | Privacy-by-default PII engine | Python, Presidio |
| 2.8 | **NQL v2.0** | Layer 4 | Full SQL compatibility + graph traversal queries | Go |
| 2.9 | **DiffEngine v1.0** | Layer 6 | Cross-signal differential analysis (BubbleUp extended) | Python |
| 2.10 | **SentinelPlane v1.0** | Layer 9 | Runtime security + CVE reachability + CSPM | eBPF, Grype, Checkov |

### Success Criteria

| KPI | Target |
|-----|--------|
| Root cause accuracy | > 85% |
| Mean time to root cause | < 5 minutes |
| Problem noise reduction | > 95% |
| TopoBrain update latency | < 500ms p99 |
| NQL query response (warm) | < 50ms p99 for 90-day |

### Tech Stack (Phase 2 additions)

```
AI/ML:         PyTorch Geometric (GNN), Prophet, LSTM, Merlion (fallback)
GenAI:         vLLM, LiteLLM (BYOM), Qwen, Llama 3
Security:      Grype (SBOM), Syft (CVE), Checkov (CSPM)
Graph:         Apache Kuzu + Redis (entity cache)
Storage:       Apache Parquet, Apache Iceberg, DuckDB
```

---

## Phase 3: Autonomy (Months 13–18)

### Goal
Surpass every competitor on autonomous remediation and prevention.

### Deliverables

| # | Component | Layer | Description | Technology |
|---|-----------|-------|-------------|------------|
| 3.1 | **SimulaX v1.0** | Layer 8 | Digital Twin + Remediation Simulation + Capacity Planning | SimPy, Redis, Optuna |
| 3.2 | **AutoHeal v3.0** | Layer 7 | Tier 3 (SimulaX-gated autonomous) + novel strategy generation | OPA, Python, Go |
| 3.3 | **AutoHeal v3.0** | Layer 7 | Tier 4 (predictive autonomous remediation) | Python |
| 3.4 | **Configuration Drift Engine** | Cross-Cutting | ArgoCD + Ansible EDA + Terraform integration | Go, Python |
| 3.5 | **GhostCollector v2.0** | Layer 2 | LLM/GenAI workload observability native | Go |
| 3.6 | **TopoBrain v3.0** | Layer 5 | Layer 7 (GenAI) + Layer 1 (Cost+Carbon) entities | Kuzu, Flink |
| 3.7 | **BusinessLens v1.0** | Layer 6 | Business transaction → IT impact mapping | Python |
| 3.8 | **CostBrain v1.0** | Layer 5 | Cost + carbon per entity, real-time | Python, Flink |
| 3.9 | **CI/CD SimulaX Gate** | Layer 8 | GitHub Actions + GitLab CI + ArgoCD integration | Go, YAML |
| 3.10 | **SimulaX v1.0** | Layer 8 | Deployment Impact Simulation + Chaos Simulation | SimPy |

### Success Criteria

| KPI | Target |
|-----|--------|
| SimulaX prediction accuracy | > 80% (vs actual post-action) |
| Automated remediation success | > 75% without human intervention |
| Mean time to remediation (Tier 3) | < 3 minutes |
| Zero false-positive autonomous actions | Never makes things worse |
| Config drift detection latency | < 60s from occurrence |

### Tech Stack (Phase 3 additions)

```
Simulation:    SimPy (discrete event), Optuna (Bayesian calibration)
Drift:         ArgoCD (K8s), Ansible EDA (OS), Terraform/OpenTofu (Cloud)
Business:      Custom Python services for revenue/SLO mapping
Cost/Carbon:   AWS Cost Explorer API, Azure Cost Management, GCP Billing API
```

---

## Phase 4: Ecosystem & Scale (Months 19–24)

### Goal
Enterprise-grade scale, compliance, and ecosystem dominance.

### Deliverables

| # | Component | Layer | Description | Technology |
|---|-----------|-------|-------------|------------|
| 4.1 | **Self-hosted deployment** | Platform | Full feature parity with SaaS | Kubernetes, Helm, ArgoCD |
| 4.2 | **SOC2 + ISO 27001** | Platform | Compliance-ready architecture | Audit logging, encryption |
| 4.3 | **Multi-region federation** | Platform | Global topology, regional data residency | K8s federation, ClickHouse clustering |
| 4.4 | **NQL v3.0** | Layer 4 | Full SQL compatibility + graph traversal | Go |
| 4.5 | **Partner integrations** | Platform | ServiceNow CMDB, GitHub, GitLab, Terraform Cloud | Go, Python |
| 4.6 | **Transparent pricing dashboard** | Layer 11 | Real-time cost tracking per tenant | React |
| 4.7 | **NexusUX v3.0** | Layer 11 | Executive mode, Mobile app, Slack-native UX | React Native |
| 4.8 | **500+ integration library** | Layer 2 | Datadog-competitive breadth | Go |
| 4.9 | **Kubernetes Operator** | Platform | Full GitOps lifecycle management | Go |
| 4.10 | **Compliance Report Generator** | Layer 10 | SOC2/ISO27001 ready evidence packages | Python |

### Success Criteria

| KPI | Target |
|-----|--------|
| Ingest throughput | 100TB/day at single-digit ms query response |
| SLA | 99.99% for SaaS |
| Time-to-value | < 30 min from signup to first insight |
| NPS | > 60 among SRE/DevOps early adopters |
| Self-hosted parity | 100% feature parity with SaaS |

### Tech Stack (Phase 4 additions)

```
Compliance:    Custom audit logging, encryption at rest/transit
Federation:    K8s federation, ClickHouse cluster replication
Integrations:  ServiceNow API, GitHub API, GitLab API, Terraform Cloud API
Mobile:        React Native
Operator:      Kubernetes Operator SDK (Go)
```

---

## Technology Stack Summary

| Category | Technologies |
|----------|-------------|
| **Collection** | eBPF (libbpf+CO-RE), Go, Rust, Protocol Buffers |
| **Stream Processing** | Apache Kafka, Apache Flink |
| **Storage** | ClickHouse, Apache Kuzu, Apache Parquet, Apache Iceberg, MinIO/S3, Redis |
| **AI/ML** | PyTorch Geometric (GNN), Prophet, LSTM, Merlion, Scikit-Learn, Optuna |
| **GenAI** | vLLM, LiteLLM, Qwen, Llama 3, GPT-4o, Claude, Gemini |
| **Policy** | Open Policy Agent (OPA) Rego |
| **Security** | eBPF LSM hooks, Grype, Syft, Checkov |
| **Config Drift** | ArgoCD, Ansible EDA, Terraform/OpenTofu |
| **Frontend** | React 19, TypeScript, FastAPI, Sigma.js, D3.js, React Native |
| **Infrastructure** | Kubernetes, Docker, Helm, ArgoCD (GitOps) |

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| eBPF kernel compatibility | High | Medium | Fallback to OTel for non-Linux targets |
| GNN training data scarcity | High | Medium | Use PyRCA as fallback for Phase 2 |
| SimulaX model accuracy | High | High | Start with 80% target, calibrate with Optuna |
| ArgoCD self-heal loops | Medium | Medium | OPA policy gates + rate limiting |
| LLM hallucination in reports | Medium | Low | Grounding guardrail + evidence validation |
| Multi-cloud API rate limits | Medium | Medium | Adaptive polling with backoff |
| ClickHouse scale limits | Low | Low | Sharding + tiered storage (Arrow/Parquet) |

---

## Team Requirements

| Role | Count | Phase |
|------|-------|-------|
| **Systems Engineer (eBPF/Go)** | 2 | Phase 1-4 |
| **Data Engineer (Flink/Kafka)** | 2 | Phase 1-4 |
| **ML Engineer (GNN/Forecasting)** | 2 | Phase 2-4 |
| **Backend Engineer (FastAPI/Python)** | 3 | Phase 1-4 |
| **Frontend Engineer (React)** | 2 | Phase 1-4 |
| **Platform Engineer (K8s/Infra)** | 2 | Phase 1-4 |
| **Security Engineer** | 1 | Phase 2-4 |
| **Product Manager** | 1 | Phase 1-4 |
| **Total** | **16** | |

---

## Success Metrics Summary

| Metric | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|---------|---------|---------|---------|
| **Ingest (TB/day)** | 1 | 10 | 50 | 100 |
| **Query latency (warm)** | <100ms | <50ms | <50ms | <10ms |
| **Root cause accuracy** | — | >85% | >85% | >90% |
| **MTTR** | — | <5min | <3min | <2min |
| **Auto-remediation rate** | — | — | >75% | >85% |
| **SimulaX accuracy** | — | — | >80% | >85% |
| **Self-hosted parity** | — | — | — | 100% |
| **Integration count** | 10 | 50 | 200 | 500+ |

---

*Document Version: 2.0 | Generated: July 2026 | Classification: Internal R&D*
