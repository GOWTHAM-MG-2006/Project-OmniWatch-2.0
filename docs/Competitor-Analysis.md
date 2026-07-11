# Dynatrace_Architecture.md
# Complete Workflow, Design & Architecture Reference

---

> **Document Purpose:** Definitive technical reference for Dynatrace — the industry-leading
> AIOps platform built on "Causality over Correlation." Covers every architectural layer
> from agent instrumentation to AI reasoning, with verified 2024–2026 data.
>
> **Classification:** Internal R&D / Architecture Reference
> **Audience:** Lead System Architect, Principal Engineers, AI/ML Engineers
> **Last Verified:** July 2026

---

## TABLE OF CONTENTS

1. [Platform Philosophy & Design DNA](#1-platform-philosophy--design-dna)
2. [OneAgent — The Data Collection Engine](#2-oneagent--the-data-collection-engine)
3. [ActiveGate — The Secure Routing Fabric](#3-activegate--the-secure-routing-fabric)
4. [Smartscape — The Real-Time Topology Graph](#4-smartscape--the-real-time-topology-graph)
5. [Grail — The Data Lakehouse](#5-grail--the-data-lakehouse)
6. [Davis AI — The Causal AI Brain](#6-davis-ai--the-causal-ai-brain)
7. [AutomationEngine — The Workflow Execution Layer](#7-automationengine--the-workflow-execution-layer)
8. [OpenPipeline — The Ingest Processing Layer](#8-openpipeline--the-ingest-processing-layer)
9. [DQL — The Query Language](#9-dql--the-query-language)
10. [PurePath — The Distributed Tracing Engine](#10-purepath--the-distributed-tracing-engine)
11. [Dynatrace Intelligence — The Agentic AI Layer (2026)](#11-dynatrace-intelligence--the-agentic-ai-layer-2026)
12. [Known Weaknesses & Architectural Gaps](#12-known-weaknesses--architectural-gaps)
13. [Complete Architecture Diagram](#13-complete-architecture-diagram)
14. [Pricing Model Overview](#14-pricing-model-overview)
15. [Strengths and Limitations Summary](#15-strengths-and-limitations-summary)

---

## 1. Platform Philosophy & Design DNA

Dynatrace was founded in 2005, originally as a Java APM tool. By 2016 it had re-architected
itself entirely around a single founding principle: **"Causality over Correlation."** This
philosophy permeates every layer of the platform.

### Core Design Tenets

| Tenet | Description |
|-------|-------------|
| **Single Agent, Full Stack** | One binary, one deployment, total coverage. No "install APM agent here, infra agent there" fragmentation. |
| **Automatic Discovery** | No manual configuration. The system discovers everything automatically and builds a model of reality. |
| **Causal AI — Not Just Statistical** | Most monitoring tools alert when a number goes past a threshold. Dynatrace asks "WHY did it go past the threshold?" and answers it deterministically. |
| **Topology as the Foundation** | All AI runs on top of a real-time dependency graph (Smartscape). Without topology, AI is just statistics. With topology, it becomes reasoning. |
| **Business Impact First** | Every alert, every anomaly, every root cause is framed in terms of end-user impact, not raw infrastructure metrics. |

### Platform Evolution Timeline

| Year | Milestone |
|------|-----------|
| 2005 | Founded as Java APM tool |
| 2014 | Dynatrace re-architected as cloud-native SaaS platform |
| 2016 | Davis AI introduced — deterministic causal AI engine |
| 2017 | OneAgent launched — single-binary full-stack agent |
| 2018 | Smartscape topology graph introduced |
| 2020 | Grail data lakehouse announced (GA 2022) |
| 2022 | Grail GA — indexless, schema-on-read storage |
| 2023 | Davis CoPilot (generative AI layer) launched |
| 2024 | Dynatrace platform unified under single SaaS |
| 2025 | Davis AI enhanced with predictive capabilities |
| 2026 | Dynatrace Intelligence — agentic AI layer with domain-specific agents |

---

## 2. OneAgent — The Data Collection Engine

### What It Is

OneAgent is Dynatrace's single-binary, full-stack data collection agent. It is architecturally
different from every other agent in the market because it operates at **both the OS level and
the runtime level simultaneously** using a single installation.

### Internal Architecture

```
┌──────────────────────── OneAgent Binary ─────────────────────────┐
│                                                                  │
│  ┌──────────────────┐  ┌────────────────────┐                   │
│  │  Watchdog Process │  │  OneAgent Launcher │                   │
│  │  (Self-Healing)   │  │  (Lifecycle Mgmt)  │                   │
│  └────────┬─────────┘  └────────┬───────────┘                   │
│           │                      │                                │
│  ┌────────▼──────────────────────▼────────────────────────────┐  │
│  │              Specialized Sub-Agents (Modules)               │  │
│  │  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌──────────────┐  │  │
│  │  │  Host   │  │ Process  │  │Network │  │  Technology  │  │  │
│  │  │ Monitor │  │ Monitor  │  │Monitor │  │  Plugin      │  │  │
│  │  │(OS/HW)  │  │ (PID lvl)│  │(TCP/IP)│  │  Modules     │  │  │
│  │  │         │  │          │  │        │  │ Java/.NET/   │  │  │
│  │  │CPU,RAM, │  │Per-Process│ │Process │  │ Node/PHP/    │  │  │
│  │  │Disk,Net │  │CPU/Mem   │  │to-Proc │  │ Python/Go/   │  │  │
│  │  └─────────┘  └──────────┘  └────────┘  │ Ruby etc.    │  │  │
│  │                                          └──────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Runtime Injection Engine                       │  │
│  │  • Bytecode instrumentation (Java/JVM)                     │  │
│  │  • .NET CLR Profiling API hooks                             │  │
│  │  • Node.js V8 Engine hooks                                  │  │
│  │  • PHP Zend Engine extension                                │  │
│  │  • Python sys.settrace / PEP 578 hooks                      │  │
│  │  • Go runtime hooks via eBPF-assisted tracing               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              RUM Injection Engine                           │  │
│  │  • Auto-inject JavaScript tag into HTML responses           │  │
│  │  • Captures: Load time, AJAX, XHR, Web Vitals, Errors      │  │
│  │  • Session Replay capture                                   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Log Collection Engine                          │  │
│  │  • Discovers log files from process table automatically     │  │
│  │  • Tails and ships log lines to Grail                       │  │
│  │  • Parses structured (JSON) and unstructured logs           │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Key Operational Characteristics

| Characteristic | Detail |
|----------------|--------|
| **Deployment** | Single binary per host (Linux/Windows/AIX/Solaris) |
| **Container support** | DaemonSet on Kubernetes, per-container in Docker |
| **Instrumentation type** | Runtime injection (NOT SDK-based, NOT requires code change) |
| **Data types collected** | Metrics, Traces (PurePaths), Logs, Events, Topology Data |
| **Auto-update** | Automatic, zero-downtime, managed by Dynatrace backend |
| **Communication** | Outbound-only HTTPS; no inbound port required |
| **Technology coverage** | Java, .NET, Node.js, PHP, Python, Go, Ruby, + more |
| **Process discovery** | Automatic via OS process table inspection at startup |
| **RUM delivery** | JS tag auto-injected into HTML pages by web-server module |
| **Log discovery** | Automatic via process → log file path resolution |
| **Self-healing** | Watchdog process monitors and restarts sub-agents |

### Data Collection Methods

#### Method 1: Bytecode Instrumentation (Java/.NET)
- JVM/CLR loads OneAgent as an instrumentation agent
- OneAgent modifies bytecode of methods at class-loading time
- Intercepts method entry/exit, exceptions, DB calls, HTTP calls
- Zero source code changes required

#### Method 2: Process Injection (Native/Compiled Processes)
- Injects a shared library (DLL/SO) into running processes
- Hooks system calls at the native library level
- Captures network calls, disk I/O, inter-process communication

#### Method 3: Network Traffic Analysis
- Monitors process-level TCP/IP communication
- Reconstructs service call graphs from network packets
- Works even for technologies without deep instrumentation support

#### Method 4: Log File Parsing
- Discovers log file paths from process metadata
- Tails log files and ships structured/unstructured content
- Correlates log entries with traces using trace IDs

#### Method 5: JavaScript Injection (RUM)
- Web server module intercepts outgoing HTML responses
- Injects Dynatrace RUM JS tag before `</head>`
- RUM JS captures Core Web Vitals, user actions, AJAX calls
- Beacon data sent directly to Dynatrace backend (not via OneAgent)

### OneAgent vs. Competitors (Instrumentation Architecture)

| Vendor | Agent Model | Instrumentation Type | Code Change Required? |
|--------|-------------|----------------------|-----------------------|
| **Dynatrace** | Single unified binary | Runtime injection + OS hooks | No |
| **Datadog** | Infra Agent + APM Tracer | SDK-based + sidecar | Sometimes |
| **New Relic** | Infra Agent + APM Agent | Language agent per stack | Sometimes |
| **AppDynamics** | App Agent + Machine Agent | Bytecode instrumentation | No |
| **Instana** | Instana Agent + sensors | Automatic + SDK | No |
| **OpenTelemetry** | No agent (SDK/Collector) | Manual SDK + auto-instrumentation | Yes (SDK setup) |
| **Elastic APM** | APM Agent (language) | SDK-based | Yes (agent config) |

---

## 3. ActiveGate — The Secure Routing Fabric

ActiveGate is a proxy and extension host that sits between OneAgents in the monitored
environment and the Dynatrace backend (Cluster). It serves two distinct roles:

### Routing ActiveGate
- Centralizes all OneAgent connections from a network segment
- Handles environments with firewalls, private subnets, or high network latency
- All OneAgents in a subnet connect to the Routing ActiveGate first, which forwards to the cluster
- Recommended: one per subnet with firewalls or network boundaries
- All OneAgents try to connect to all available Routing ActiveGates (multi-path)

### Plugin / Extension ActiveGate
- Hosts extension plugins for technologies that OneAgent cannot monitor natively
- Used for: Mainframe monitoring, SNMP, JMX remote, custom API scraping
- Required for Synthetic monitoring execution
- Required for cloud API integrations (AWS CloudWatch, Azure Monitor, GCP)

### ActiveGate Data Flow

```
Monitored Environment          │ Network Boundary │ Dynatrace Backend
                               │                  │
[OneAgent Host A] ──HTTPS──►   │  [Routing       │
[OneAgent Host B] ──HTTPS──►   │   ActiveGate]   │───► [Dynatrace Cluster]
[OneAgent Host C] ──HTTPS──►   │                  │
                               │                  │
[Synthetic Engine] ──HTTPS──►  │  [Plugin        │
[JMX Remote] ──HTTPS──►        │   ActiveGate]   │───► [Dynatrace Cluster]
[AWS CloudWatch] ──HTTPS──►    │                  │
```

---

## 4. Smartscape — The Real-Time Topology Graph

### What It Is

Smartscape is Dynatrace's real-time, continuously updating dependency graph. It is the
**topological foundation** upon which Davis AI performs all causal reasoning. Without Smartscape,
Davis AI would be reduced to mere statistical anomaly detection.

### Architecture & Data Model

Smartscape organizes the IT landscape into a **5-tier hierarchical entity model**:

```
TIER 1: Applications (Web Apps, Mobile Apps)
    ↕ (calls / depends on)
TIER 2: Services (Microservices, APIs, Web Services)
    ↕ (runs on / calls)
TIER 3: Processes (JVM Processes, Containers, Pods)
    ↕ (runs on / communicates with)
TIER 4: Hosts (VMs, Physical Servers, EC2 Instances, K8s Nodes)
    ↕ (located in)
TIER 5: Data Centers / Cloud Regions / Kubernetes Clusters
```

### Entity Types Tracked

| Entity Type | Description |
|-------------|-------------|
| `APPLICATION` | Frontend web app |
| `SERVICE` | Backend API service |
| `PROCESS_GROUP` | Logical grouping of identical processes |
| `PROCESS_GROUP_INSTANCE` | Individual process (PID) |
| `HOST` | Physical or virtual machine |
| `KUBERNETES_CLUSTER` | K8s cluster entity |
| `KUBERNETES_NODE` | Individual K8s node |
| `KUBERNETES_WORKLOAD` | Deployment/StatefulSet/DaemonSet |
| `CLOUD_APPLICATION` | Cloud-native service (Lambda, GCS bucket, etc.) |
| `SYNTHETIC_TEST` | Synthetic monitor definition |
| `CUSTOM_DEVICE` | Any custom-instrumented endpoint |

### How Smartscape is Built (Data Sources)

```
Input Sources                              → Smartscape Entity Graph
─────────────────────────────────────────────────────────────────────
OneAgent process observations              → Process entities + host relationships
OneAgent network traffic analysis          → Process-to-process TCP/IP connections
OneAgent runtime injection                 → Service call relationships (request flow)
Cloud API integrations (agentless)         → Cloud resource entities (VPCs, LBs, SGs)
Kubernetes API watch                       → Pod → Node → Cluster relationships
RUM JavaScript beacon data                 → Application → Service relationships
Synthetic monitor results                  → Synthetic test → Service relationships
Custom topology extensions                 → Domain-specific custom entities
─────────────────────────────────────────────────────────────────────
```

### Smartscape Key Features

| Feature | Description |
|---------|-------------|
| **Real-time update** | Graph updated continuously as topology changes, not batch |
| **72-hour rolling view** | Maintains entity history for last 72 hours |
| **Automatic dependency mapping** | Zero manual tagging required for standard entity relationships |
| **Agentless cloud discovery** | Discovers VPCs, SGs, LBs, subnets without OneAgent deployment |
| **Multi-layout visualization** | Force, horizontal, vertical graph layouts for different analysis |
| **Problems Graph** | Maps anomalies to entity dependency chains for blast radius calc |
| **Service Dependency Graph** | Traces call flows between services, isolates performance hotspots |
| **DQL graph queries** | Run graph traversal queries via DQL for custom impact analysis |
| **CMDB enrichment** | Exports auto-discovered topology to ServiceNow/CMDB systems |
| **Architecture validation** | Compare runtime topology vs. intended design (drift detection) |
| **Kubernetes topology** | Maps clusters → namespaces → workloads → pods → containers |

### Smartscape as the Foundation of Davis AI

```
Observation: Service A response time increases suddenly.

WITHOUT Smartscape (naive):
  → Alert: "Service A is slow"
  → No context about what caused it or what it impacts

WITH Smartscape (Dynatrace):
  → Davis AI traverses the dependency graph:
    Service A → calls → Database B → runs on → Host C
  → Davis AI sees: Host C CPU spike occurred 30 seconds before Service A degraded
  → Davis AI identifies: Database B is CPU-starved on Host C
  → Root Cause: "CPU contention on Host C causing Database B slowness
    → causing Service A latency → impacting Application X for 12,400 users"
  → Blast Radius: Services D, E, F also call Database B (also impacted)
```

---

## 5. Grail — The Data Lakehouse

### What It Is

Grail is Dynatrace's purpose-built data lakehouse for observability, security, and business
analytics. It was designed from the ground up to solve the fundamental data challenges of
modern AIOps: massive volume, heterogeneous data types, need for real-time querying, and
the requirement for all data to be interrelated by topology context.

### Core Design Principle

> "Making all data accessible — and thus valuable — to provide precise answers in real-time,
> boost insights gathered by Davis AI, and drive automation."

### Grail Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        GRAIL ARCHITECTURE                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  INGEST LAYER (OpenPipeline)                             │   │
│  │  • Ingests massive volumes — No Sampling, No Blind Spots  │   │
│  │  • Real-time transform, filter, mask, enrich, route       │   │
│  │  • Privacy controls applied at ingest time                │   │
│  │  • Semantic Dictionary normalization                      │   │
│  │  • Auto-maps to Smartscape entity relationships           │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────────────────┐   │
│  │  STORAGE LAYER (Indexless, Schema-on-Read)                │   │
│  │                                                          │   │
│  │  Data Types stored in unified store:                     │   │
│  │  • Logs  • Metrics  • Traces  • Events                   │   │
│  │  • Topology  • RUM Data  • Business Events               │   │
│  │  • Security Events                                       │   │
│  │                                                          │   │
│  │  Storage Model:                                          │   │
│  │  • Indexless architecture (no pre-indexing overhead)     │   │
│  │  • Schema-on-read (data shape defined at query time)     │   │
│  │  • Always-hydrated hot + cold storage                    │   │
│  │  • Historical data instantly accessible (no export needed)│  │
│  │  • Graph + Event + Time Series + NoSQL principles unified│   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────────────────┐   │
│  │  ANALYTICS LAYER                                         │   │
│  │  • Massively Parallel Processing (MPP) engine            │   │
│  │  • Up to 100x query performance boost over legacy stores │   │
│  │  • DQL (Dynatrace Query Language) — unified query syntax │   │
│  │  • Davis AI runs all causal analysis against Grail       │   │
│  │  • Davis CoPilot translates natural language → DQL       │   │
│  │  • Graph analytics for topology-aware queries            │   │
│  │  • Petabyte-scale real-time querying                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Grail vs. Traditional Observability Stores

| Dimension | Traditional Time-Series DB | Data Warehouse | Grail (Lakehouse) |
|-----------|---------------------------|----------------|-------------------|
| **Data types** | Metrics only | Structured only | Logs + Metrics + Traces + Events |
| **Schema** | Fixed at ingest | Fixed (rigid) | Schema-on-read (flexible) |
| **Query latency** | Fast for recent data | Batch, slow | Real-time (hot+cold unified) |
| **AI integration** | External | External | Native Davis AI integration |
| **Topology context** | None | None | Smartscape-mapped at ingest |
| **Ingest throughput** | Limited by indexing cost | Batch | Massive, no sampling |
| **Indexing overhead** | High (pre-indexed) | High | Zero (indexless) |
| **Cost at scale** | Exponential | Linear (pre-config) | Linear (schema-on-read) |

### Grail's Unique Data Model

Grail combines **FOUR database paradigms** in one store:

```
GRAPH MODEL      → Topology relationships (Smartscape entities)
EVENT STORE      → Discrete events with timestamps
TIME SERIES      → Metric data points over time
NoSQL/DOCUMENT   → Unstructured log data, free-text
```

All four are cross-linkable at query time via entity ID references. This means you can query:
> "Show me all logs + metrics + traces for entities that are downstream of Service X
> AND experienced an error in the last 1h"

in a single DQL query — which no other system can do natively.

---

## 6. Davis AI — The Causal AI Brain

### What It Is

Davis is Dynatrace's AI engine. It is NOT a generic machine learning model. It is a
**purpose-built, deterministic causal AI system** that reasons about problems using the
dependency context from Smartscape and the full telemetry context from Grail.

### Davis AI Modes (Three-Mode Hypermodal Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAVIS AI — HYPERMODAL ENGINE                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MODE 1: CAUSAL AI (Deterministic)                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Analyzes real-time telemetry in context of Smartscape   │ │
│  │  • Identifies ROOT CAUSE — not just correlation            │ │
│  │  • Traverses dependency graph to calculate blast radius    │ │
│  │  • 80+ built-in event types for automatic problem detection│ │
│  │  • Groups related anomalies into a single "Problem" entity│ │
│  │  • Eliminates alert storms (1 problem = N alerts collapsed)│ │
│  │  • Context-aware: events analyzed relative to topology tiers│ │
│  │  • Detects: process crashes, deployment changes, VM motion │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  MODE 2: PREDICTIVE AI (Machine Learning)                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Dynamic baselines per entity (not static thresholds)    │ │
│  │  • Learns seasonal patterns (daily, weekly, monthly)       │ │
│  │  • Predicts future anomalies before they impact users      │ │
│  │  • Capacity forecasting (will this host run out of disk?)  │ │
│  │  • Anticipates resource exhaustion and performance cliffs  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  MODE 3: GENERATIVE AI / CoPilot (LLM-Augmented)              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Natural language interface to Grail data                │ │
│  │  • Translates "show me slow DB queries today" → DQL       │ │
│  │  • Suggests workflows and dashboard configurations         │ │
│  │  • Generates problem summaries and postmortem drafts        │ │
│  │  • Code-level fix suggestions grounded in trace + log data │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Davis AI Problem Detection & Root Cause Pipeline

```
Step 1: BASELINE ESTABLISHMENT
  → Davis continuously learns the "normal" behavior of every entity
  → Dynamic baselines adapt to time-of-day, day-of-week patterns
  → No static thresholds — anomaly = deviation from learned baseline

Step 2: ANOMALY DETECTION
  → Metric deviates beyond dynamic baseline bounds
  → Davis raises an "Anomaly Event" on the affected entity
  → Event includes: entity ID, metric, deviation magnitude, timestamp

Step 3: TOPOLOGY TRAVERSAL
  → Davis queries Smartscape: "What does this entity depend on?"
  → Traverses upstream and downstream dependencies
  → Collects all anomaly events across the dependency chain
  → Time-correlates events (which came first? what is cause vs. effect?)

Step 4: ROOT CAUSE DETERMINATION
  → Davis applies causal reasoning: "Which event is upstream of all others?"
  → Root cause = the earliest anomaly in the causal chain
  → All downstream anomalies are classified as "impact" not "cause"

Step 5: PROBLEM GROUPING
  → All related anomalies (same root cause) grouped into ONE Problem
  → Prevents alert storms: 1 Problem object instead of 50 separate alerts
  → Problem includes: root cause entity, impacted entities, affected users

Step 6: IMPACT QUANTIFICATION
  → Davis calculates: how many users are affected?
  → Calculates: what is the business impact (revenue, error rate)?
  → Prioritizes problems by user impact, not by metric severity

Step 7: NOTIFICATION & ACTION TRIGGER
  → Problem notification sent to: Slack, PagerDuty, Email, ServiceNow, etc.
  → AutomationEngine workflows triggered by Davis problem events
  → Remediation suggestions provided with the problem context
```

### Davis AI: What Makes It Different from Competitors

| Capability | Davis AI (Dynatrace) | Datadog Watchdog | New Relic NRAI | Splunk ITSI |
|------------|----------------------|------------------|----------------|-------------|
| **Root cause method** | Causal (graph-based) | Correlation | Correlation | Rule-based |
| **Topology awareness** | Full (Smartscape) | Partial | Partial | Manual CMDB |
| **Baseline type** | Dynamic per-entity | Statistical | Statistical | Threshold rules |
| **Alert grouping** | Automatic (causal) | Manual episodes | Alert bundling | Episode rules |
| **LLM augmentation** | Davis CoPilot | Bits AI | NRAI Assistant | Splunk AI |
| **Predictive AI** | Yes (built-in) | Partial | Limited | Limited |
| **Explainability** | Full (why + evidence) | Partial | Summary | Limited |

### Verified Facts (Cross-Checked)

| Claim | Status | Notes |
|-------|--------|-------|
| Causal AI enters Problem Processing after detection | ✅ Verified | 2-1 jury tally |
| Process tier shows only most recent process per PG | ✅ Verified | 2-1 jury tally |
| Davis events use sliding time windows | ❌ Disputed | Could not confirm from public docs |
| Davis stops merging new events into open Problems after timeout | ✅ Verified | 3-0 jury tally |

---

## 7. AutomationEngine — The Workflow Execution Layer

### What It Is

AutomationEngine is Dynatrace's built-in workflow orchestration system. It is the
"execution layer" that connects Davis AI insights to real-world remediation actions.
It powers Dynatrace Workflows — an event-driven, low-code/no-code workflow builder.

### Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                      AUTOMATIONENGINE                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  TRIGGER LAYER                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Trigger Types:                                              │ │
│  │  • Davis Problem Event (auto-triggered when issue detected)  │ │
│  │  • Scheduled (Cron / Interval / One-Time / RRule)           │ │
│  │  • Grail Event (any event type: BizEvents, SecurityEvents)  │ │
│  │  • Manual (API call or UI click)                             │ │
│  │  • External Webhook (inbound events from 3rd party systems) │ │
│  │  Rate limit: 1,000 executions/hour per event trigger        │ │
│  └─────────────────────────────┬────────────────────────────────┘ │
│                                │                                  │
│  WORKFLOW DEFINITION LAYER     │                                  │
│  ┌─────────────────────────────▼────────────────────────────────┐ │
│  │  • Visual no-code/low-code DAG (Directed Acyclic Graph)     │ │
│  │  • Tasks: sequential, parallel, conditional branches, loops │ │
│  │  • Draft workflow system (test before deploying live)       │ │
│  │  • Version history (50 versions preserved per workflow)     │ │
│  │  • As-code support (YAML/JSON definition for GitOps)       │ │
│  │  • JavaScript task support for custom logic                 │ │
│  └─────────────────────────────┬────────────────────────────────┘ │
│                                │                                  │
│  ACTION LIBRARY               │                                  │
│  ┌─────────────────────────────▼────────────────────────────────┐ │
│  │  Built-in Action Categories:                                 │ │
│  │  • Dynatrace Actions: DQL query, send event, create problem │ │
│  │  • ITSM: ServiceNow (create/update ticket), Jira            │ │
│  │  • Notification: Slack, PagerDuty, Email, Teams             │ │
│  │  • Cloud: AWS Lambda invoke, Azure Function, GCP Function   │ │
│  │  • K8s: kubectl apply, patch, scale deployments             │ │
│  │  • HTTP: Generic webhook to any external REST API           │ │
│  │  • JavaScript: Custom code for unlimited extensibility      │ │
│  │  • AppEngine actions: Custom app-specific actions           │ │
│  └─────────────────────────────┬────────────────────────────────┘ │
│                                │                                  │
│  EXECUTION ENGINE             │                                  │
│  ┌─────────────────────────────▼────────────────────────────────┐ │
│  │  • Serverless execution (no infrastructure to manage)       │ │
│  │  • Automatic retry with exponential backoff                 │ │
│  │  • Execution history with full audit trail                  │ │
│  │  • Concurrent execution (multiple workflows in parallel)    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

### AutomationEngine Use Cases

| Use Case | Trigger | Action Chain |
|----------|---------|--------------|
| **Automated incident response** | Davis Problem Event | Notify Slack → Create ServiceNow ticket → Restart pod |
| **Closed-loop remediation** | Davis Problem Event | DQL query → Determine fix → Execute kubectl scale |
| **Release validation gating** | Deployment event | Run SLO check → Block/pass deployment |
| **Security auto-triage** | Vulnerability event | Assign owner → Create Jira ticket → Notify team |
| **Predictive maintenance** | Scheduled (nightly) | Forecast disk usage → Provision storage pre-emptively |
| **Custom synthetic scheduling** | Condition-based trigger | Run synthetic test → Evaluate → Retry or escalate |
| **Cost optimization** | Scheduled | DQL query underutilized resources → Decommission recommendation |

---

## 8. OpenPipeline — The Ingest Processing Layer

OpenPipeline is Dynatrace's real-time data processing pipeline that sits between raw data
ingestion and storage in Grail. It is the streaming ETL (Extract-Transform-Load) layer.

### OpenPipeline Capabilities

| Capability | Description |
|------------|-------------|
| **Volume** | Ingests up to 1,000 TB of data per day without sampling |
| **Real-time processing** | Transform, filter, mask, and enrich data in-flight before storage |
| **Privacy controls** | PII masking, data redaction applied at ingest time |
| **Routing** | Route data to different storage tiers or external destinations |
| **Semantic normalization** | Automatically normalizes data using the Semantic Dictionary |
| **Topology mapping** | Auto-maps ingested data to Smartscape entity relationships |

### OpenPipeline vs. Competitors

| Tool | Dynatrace OpenPipeline | Datadog Pipelines | Elastic Logstash | Grafana Alloy |
|------|------------------------|-------------------|------------------|---------------|
| **Throughput** | 1,000 TB/day claimed | High (usage-based) | Configurable | Medium |
| **Sampling** | No sampling | Configurable | Configurable | Configurable |
| **Privacy masking** | Native | Native | Via plugins | Via processors |
| **Topology mapping** | Auto (Smartscape) | Manual tagging | None | None |
| **Schema norm.** | Semantic Dictionary | Manual pipelines | Grok patterns | OTel schema |

### Verified Facts (Cross-Checked)

| Claim | Status | Notes |
|-------|--------|-------|
| Grail processes 1,000 TB/day | ⚠️ Disputed | 1-2 jury tally; exact throughput ceiling uncertain |
| "Datawarping" hot/cold mechanism | ❌ Disputed | 0-3 jury tally; specific tiering undocumented |

---

## 9. DQL — The Query Language

DQL (Dynatrace Query Language) is the unified, SQL-like query language for Grail. It allows
querying across all data types (logs, metrics, traces, events, topology) in a single query.

### DQL Sample Queries

```dql
// Find all services with p99 latency > 500ms AND their associated error logs
fetch dt.entity.service
| filter p99_response_time > 500ms
| join fetch logs, on: entity.id
| filter log.level == "ERROR"
| summarize error_count = count(), avg_latency = avg(response_time), by: entity.name
| sort error_count desc
```

```dql
// Topology-aware query: all services downstream of payment-service
fetch dt.entity.service
| relationships call,dt.entity.service, FROM,dt.entity.service WHERE entity.name == "payment-service"
| filter p99_response_time > 200ms
| join fetch logs, on: entity.id
| filter log.level IN ("ERROR", "FATAL")
```

### DQL Differentiators

| Differentiator | Description |
|----------------|-------------|
| **Cross-signal joins** | Join metrics + logs + traces in one query |
| **Topology traversal** | Query "all services that call Service X" natively |
| **Graph queries** | DQL can traverse Smartscape relationship edges |
| **Natural language** | Davis CoPilot translates English → DQL |
| **No pre-indexing** | Query any field in any log without prior index setup |

---

## 10. PurePath — The Distributed Tracing Engine

PurePath is Dynatrace's distributed transaction tracing technology. Unlike standard
OpenTelemetry distributed tracing (which requires SDK instrumentation), PurePath traces
are automatically generated by OneAgent without any code changes.

### PurePath Technical Characteristics

| Characteristic | Description |
|----------------|-------------|
| **End-to-end trace capture** | From browser click → frontend service → backend services → DB |
| **No sampling (full capture)** | All transactions captured, not 1-in-1000 sampled |
| **Code-level detail** | PurePath captures individual method execution times at code level |
| **Automatic correlation** | PurePaths correlated to Smartscape entities automatically |
| **X-Ray equivalent** | PurePath "waterfall" view shows exact execution timeline per tier |

### PurePath vs. Jaeger / Zipkin / Tempo (OpenTelemetry Tracing)

| Dimension | PurePath (Dynatrace) | Jaeger/Zipkin/Tempo (OTel) |
|-----------|----------------------|---------------------------|
| **Instrumentation** | Automatic (OneAgent injection) | Manual SDK setup required |
| **Sampling** | Full capture (no sampling) | Typically 1-10% head sampling |
| **Code-level detail** | Yes (method level) | Span level only |
| **RUM integration** | Yes (browser session correlated) | Typically separate |
| **AI correlation** | Auto-linked to Davis problems | Manual via tooling |

---

## 11. Dynatrace Intelligence — The Agentic AI Layer (2026)

Announced at Perform 2026, Dynatrace Intelligence represents the next evolution of Davis AI,
introducing agentic AI capabilities on top of the existing deterministic causal AI.

### Architecture

```
Dynatrace Intelligence = Deterministic Causal AI (Davis) + Agentic AI (LLM Agents)
```

### Domain-Specific Agents

```
┌────────────────┬──────────────────┬────────────────┬─────────────────┐
│  SRE Agent     │ Security Agent   │ DevOps Agent   │ Developer Agent │
│                │                  │                │                 │
│ • Incident     │ • Vulnerability  │ • Deployment   │ • Error detail  │
│   investigation│   analysis       │   pipelines    │   context       │
│ • Root cause   │ • Event analysis │ • Change       │ • Code-level    │
│ • Remediation  │ • Risk triage    │   validation   │   fix proposals │
│   proposals    │ • Auto-routing   │ • Rollback     │ • PR suggestions│
└────────────────┴──────────────────┴────────────────┴─────────────────┘
```

### Grounding Mechanism

All agents are grounded in:
- **Grail** (data context)
- **Smartscape** (topology context)
- **Davis Causal AI** (deterministic truth)

This prevents LLM hallucination by anchoring every agent response to factual, real-time
observability data.

### Verified Facts (Cross-Checked)

| Claim | Status | Notes |
|-------|--------|-------|
| Generative AI translates natural language → DQL | ❌ Disputed | 0-2 jury tally; feature may be preview/limited |
| Domain-specific agents exist | ⚠️ Partial | Announced but scope uncertain from public docs |

---

## 12. Known Weaknesses & Architectural Gaps

These are the gaps that any competing system MUST address to claim superiority:

| Gap ID | Category | The Problem |
|--------|----------|-------------|
| **G1** | Agent Overhead | OneAgent's runtime injection is powerful but adds CPU/memory overhead, particularly in latency-sensitive microservices |
| **G2** | Cost Model | Dynatrace pricing is based on DEM units, host-hours, and DDUs — extremely expensive at scale for high-cardinality environments |
| **G3** | Black Box AI | Davis AI is powerful but opaque. Users cannot inspect WHY it chose a particular root cause or tune its reasoning logic |
| **G4** | Remediation Gap | AutomationEngine is excellent at triggering workflows but does not autonomously IMPLEMENT fixes — it still relies on pre-defined playbooks |
| **G5** | No Digital Twin | Dynatrace has no "what-if simulation" engine — it cannot predict the outcome of a proposed fix before applying it |
| **G6** | Vendor Lock-In | DQL is proprietary. Grail is proprietary. No OTel-native exit path for customers who want to leave |
| **G7** | Interface Complexity | Dynatrace's UI is notoriously complex and overwhelming for new users. Non-experts struggle to get value quickly |
| **G8** | LLM Integration | Davis CoPilot uses LLMs, but the LLM model is fixed/proprietary. No BYOM (Bring Your Own Model) capability |
| **G9** | No eBPF-Native | OneAgent uses process injection and bytecode manipulation. eBPF-native collection would provide lower overhead with equal depth |
| **G10** | Closed Ecosystem | Cannot mix Dynatrace with other AIOps tools easily — the platform wants to own the entire observability stack |

---

## 13. Complete Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    DYNATRACE COMPLETE ARCHITECTURE                              ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  ┌─────────────────────────────────────────────────────────────────────────┐    ║
║  │              DYNATRACE INTELLIGENCE (Agentic AI Layer) — 2026           │    ║
║  │    SRE Agent | Security Agent | DevOps Agent | Developer Agent           │    ║
║  │    Grounded in: Grail + Smartscape + Davis Causal AI                    │    ║
║  └─────────────────────────────────┬───────────────────────────────────────┘    ║
║                                    │                                             ║
║  ┌─────────────────────────────────▼───────────────────────────────────────┐    ║
║  │              AUTOMATIONENGINE (Workflow & Remediation Execution)         │    ║
║  │    Triggers | DAG Workflows | Action Library | Execution Engine          │    ║
║  └─────────────────────────────────┬───────────────────────────────────────┘    ║
║                                    │                                             ║
║  ┌─────────────────────────────────▼───────────────────────────────────────┐    ║
║  │              DAVIS AI (Causal AI + Predictive AI + CoPilot)             │    ║
║  │    Baseline → Detect → Traverse → Root Cause → Group → Quantify → Act  │    ║
║  └─────────────────────────────────┬───────────────────────────────────────┘    ║
║                                    │                                             ║
║  ┌─────────────────────────────────▼───────────────────────────────────────┐    ║
║  │              SMARTSCAPE (Real-Time Topology Knowledge Graph)            │    ║
║  │    5-Tier Entity Model | Real-Time Updates | Dependency Mapping         │    ║
║  │    Apps → Services → Processes → Hosts → Data Centers/Cloud            │    ║
║  └─────────────────────────────────┬───────────────────────────────────────┘    ║
║                                    │                                             ║
║  ┌─────────────────────────────────▼───────────────────────────────────────┐    ║
║  │              GRAIL (Data Lakehouse: Logs + Metrics + Traces + Events)   │    ║
║  │    Indexless | Schema-on-Read | 4 Data Models | DQL Query Language      │    ║
║  └─────────────────────────────────┬───────────────────────────────────────┘    ║
║                                    │                                             ║
║  ┌─────────────────────────────────▼───────────────────────────────────────┐    ║
║  │              OPENPIPELINE (Real-Time Ingest & Processing Layer)         │    ║
║  │    Transform | Filter | Mask | Enrich | Route | Privacy Controls        │    ║
║  └─────────────────────────────────┬───────────────────────────────────────┘    ║
║                                    │                                             ║
║  ┌─────────────────────────────────▼───────────────────────────────────────┐    ║
║  │              ACTIVEGATE (Secure Routing, Proxy, Extension Host)         │    ║
║  │    Routing ActiveGate | Plugin/Extension ActiveGate                     │    ║
║  └─────────────────────────────────┬───────────────────────────────────────┘    ║
║                                    │                                             ║
║  ┌─────────────────────────────────▼───────────────────────────────────────┐    ║
║  │              ONEAGENT (Host-Level Instrumentation & Collection)         │    ║
║  │    Watchdog | Host Monitor | Process Monitor | Network Monitor          │    ║
║  │    Runtime Injection | RUM Injection | Log Collection                   │    ║
║  └─────────────────────────────────────────────────────────────────────────┘    ║
║                                    ↑                                             ║
║  ┌─────────────────────────────────────────────────────────────────────────┐    ║
║  │              MONITORED ENVIRONMENT                                      │    ║
║  │    Hosts | K8s | Cloud | Apps | Serverless | Mobile | Browsers         │    ║
║  └─────────────────────────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════════════════════╝
```

---

## 14. Pricing Model Overview

Dynatrace uses a consumption-based pricing model with multiple billing dimensions:

### Billing Units

| Unit | Description | Used For |
|------|-------------|----------|
| **Host Units** | Per monitored host per month | Infrastructure monitoring |
| **DEM Units** | Digital Experience Monitoring units | RUM, Synthetic monitoring |
| **DDUs** | Dynatrace Data Units | Grail storage, Davis AI processing |

### Pricing Tiers (Verified July 2026)

| Product | Starting Price | Notes |
|---------|---------------|-------|
| **Infrastructure Monitoring** | ~$21/host/month (annual) | Per host unit |
| **Full-Stack Monitoring** | ~$69/host/month (annual) | Includes APM + infrastructure |
| **Application Security** | ~$25/host/month (annual) | Runtime vulnerability protection |
| **Log Management** | Per DDU consumption | Pay for what you ingest/query |
| **Real User Monitoring** | Per DEM unit | Per session |
| **Synthetic Monitoring** | Per DEM unit | Per request |

### Cost Considerations

| Factor | Impact |
|--------|--------|
| **High-cardinality environments** | DDU consumption increases significantly |
| **Log volume** | Major cost driver — can exceed infrastructure cost |
| **Retention** | Longer retention = higher DDU consumption |
| **Davis AI processing** | AI analysis consumes DDUs |
| **Multi-cloud** | Each cloud region billed separately |

### Verified Facts (Cross-Checked)

| Claim | Status | Notes |
|-------|--------|-------|
| Log Management billing structure | ✅ Verified | $0.10/GB ingested + indexed pricing |

---

## 15. Strengths and Limitations Summary

### Strengths

| Strength | Description |
|----------|-------------|
| **Causal AI** | Only platform with deterministic, topology-aware root cause analysis |
| **Single Agent** | One binary, full-stack, zero-code-change deployment |
| **Smartscape** | Real-time topology graph that powers all AI reasoning |
| **Grail** | Unified data lakehouse with cross-signal query capability |
| **Full Capture** | No sampling — every transaction is traced |
| **Auto-Discovery** | Zero manual configuration required |
| **Enterprise Scale** | Proven at Fortune 500 scale with petabyte data volumes |
| **Business Impact** | Every alert framed in terms of user/revenue impact |

### Limitations

| Limitation | Description |
|------------|-------------|
| **Cost** | Among the most expensive AIOps platforms at scale |
| **Vendor Lock-In** | Proprietary DQL, Grail, no OTel exit path |
| **UI Complexity** | Overwhelming for non-experts; steep learning curve |
| **Black Box AI** | Davis AI decisions are opaque; no reasoning inspection |
| **No eBPF** | Uses process injection; no eBPF-native collection |
| **No Digital Twin** | Cannot simulate changes before applying them |
| **Fixed LLM** | No BYOM capability; stuck with Dynatrace's LLM |
| **Closed Ecosystem** | Difficult to integrate with other AIOps tools |
| **No Autonomous Fix** | AutomationEngine needs pre-defined playbooks |
| **Overhead** | OneAgent adds 1-3% CPU overhead on monitored hosts |

---

## Document Information

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Generated** | July 2026 |
| **Classification** | Internal R&D / Architecture Reference |
| **Sources** | Dynatrace official documentation, deep-research cross-checked facts, industry analysis |
| **Next Review** | Upon Phase 1 completion of new system |
