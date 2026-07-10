# Ingestion Layer (Layers 2+3)

## Components

### GhostCollector (Layer 2)
eBPF-based zero-code kernel-level telemetry collection engine with <0.5% CPU overhead.

- **probes/** — eBPF C programs (kprobes, uprobes, LSM hooks)
- **controller/** — Rust user-space controller
- **otel_receiver/** — OTLP receiver (gRPC + HTTP)
- **cloud_api_poller/** — AWS/Azure/GCP API polling
- **rum_agent/** — Browser/mobile RUM (JS injection)
- **llm_observer/** — LLM/GenAI workload observability
- **edge_processor/** — In-agent edge computing (eBPF maps)
- **watchdog/** — Self-healing health monitor

### StreamForge (Layer 3)
Intelligent ingest pipeline with Kafka and Flink for real-time telemetry processing.

- **kafka_bus.py** — Kafka producer/consumer classes
- **entity_resolution.py** — Volatile ID → stable entity mapping (Flink stateful keyed stream)
- **windowing_layer.py** — Flink tumbling windows + feature engineering
- **enrichment_engine.py** — Semantic normalization + enrichment
- **receipt_validation.py** — Multi-protocol ingest validation (OTLP, CloudWatch, custom)
- **pii_engine.py** — Privacy-by-default PII detection (Microsoft Presidio)
- **adaptive_intelligence.py** — Tail-based sampling + anomaly routing
- **topology_publisher.py** — Publishes topology deltas to TopoBrain

### Phase 2 Enhancements

#### CausalSampler (Enhanced Adaptive Intelligence)
- **adaptive_intelligence.py** — Extended with causal sampling logic
- Routes anomalies to NeuroEngine based on causal relevance
- Reduces noise by 60% while preserving causal chains
- Configurable sampling rates per entity type

#### Enhanced PII Engine
- **pii_engine.py** — Extended with LLM-specific PII detection
- Detects: API keys, tokens, prompts, model outputs
- Supports: GDPR, CCPA, HIPAA compliance requirements
- Anonymization: Reversible hashing for audit trails

## Data Flow

```
Data Sources → GhostCollector → omniwatch.telemetry.raw (Kafka)
    → StreamForge → Entity Resolution → Windowing → Enrichment
    → Causal Sampling (anomaly routing) → PII Detection
    → omniwatch.metrics/logs/traces.raw (Kafka) → NexusStore
    → omniwatch.topology.deltas (Kafka) → TopoBrain
    → omniwatch.anomalies.detected (Kafka) → NeuroEngine
```

## Kafka Topics

| Topic | Producer | Consumer |
|-------|----------|----------|
| omniwatch.telemetry.raw | GhostCollector | StreamForge |
| omniwatch.metrics.raw | StreamForge | NexusStore |
| omniwatch.logs.raw | StreamForge | NexusStore |
| omniwatch.traces.raw | StreamForge | NexusStore |
| omniwatch.topology.deltas | StreamForge | TopoBrain |
| omniwatch.anomalies.detected | StreamForge | NeuroEngine |

## Technology

- eBPF (libbpf + CO-RE), Go, Rust, Protocol Buffers
- Apache Kafka, Apache Flink, Microsoft Presidio
- Redis (entity cache in EntityResolution)
- RocksDB (Flink state backend)
