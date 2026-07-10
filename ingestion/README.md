# Ingestion Layer (Layers 2+3)

## Components

### GhostCollector (Layer 2)
eBPF-based zero-code kernel-level telemetry collection engine.

- **probes/** — eBPF C programs (kprobes, uprobes, LSM hooks)
- **controller/** — Rust user-space controller
- **otel_receiver/** — OTLP receiver (gRPC + HTTP)
- **cloud_api_poller/** — AWS/Azure/GCP API polling
- **rum_agent/** — Browser/mobile RUM (JS injection)
- **llm_observer/** — LLM/GenAI workload observability
- **edge_processor/** — In-agent edge computing (eBPF maps)
- **watchdog/** — Self-healing health monitor

### StreamForge (Layer 3)
Intelligent ingest pipeline with Kafka and Flink.

- **kafka_bus.py** — Kafka producer/consumer classes
- **entity_resolution.py** — Volatile ID → stable entity mapping
- **windowing_layer.py** — Flink tumbling windows + feature engineering
- **enrichment_engine.py** — Semantic normalization + enrichment
- **receipt_validation.py** — Multi-protocol ingest validation
- **pii_engine.py** — Privacy-by-default PII detection (Presidio)
- **adaptive_intelligence.py** — Tail-based sampling + anomaly routing
- **topology_publisher.py** — Publishes topology deltas to TopoBrain

## Data Flow

```
Data Sources → GhostCollector → omniwatch.telemetry.raw (Kafka)
    → StreamForge → Entity Resolution → Windowing → Enrichment
    → omniwatch.metrics/logs/traces.raw (Kafka) → NexusStore
```

## Technology

- eBPF (libbpf + CO-RE), Go, Rust, Protocol Buffers
- Apache Kafka, Apache Flink, Microsoft Presidio
