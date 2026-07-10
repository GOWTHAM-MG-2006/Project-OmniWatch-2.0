-- OmniWatch 2.0 — ClickHouse Schema
-- Component: NexusStore Schema Definitions
-- Layer: 4 (Storage)
-- Purpose: All ClickHouse table definitions for the warm storage tier

CREATE DATABASE IF NOT EXISTS omniwatch;

-- ─── Metrics (Time-Series) ─────────────────────────────────────────
-- Primary query: By entity_id + time range
CREATE TABLE IF NOT EXISTS omniwatch.metrics
(
    entity_id       String,
    entity_type     LowCardinality(String),
    entity_layer    UInt8,
    metric_name     String,
    metric_value    Float64,
    metric_unit     LowCardinality(String),
    tags            Map(String, String),
    timestamp       DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (entity_id, metric_name, timestamp)
SETTINGS index_granularity = 8192;

-- ─── Logs ───────────────────────────────────────────────────────────
-- Primary query: By entity_id + log_level
CREATE TABLE IF NOT EXISTS omniwatch.logs
(
    entity_id       String,
    entity_type     LowCardinality(String),
    service_name    String,
    log_level       LowCardinality(String),
    message         String,
    trace_id        Nullable(String),
    span_id         Nullable(String),
    attributes      Map(String, String),
    timestamp       DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (entity_id, log_level, timestamp)
SETTINGS index_granularity = 8192;

-- ─── Traces (Distributed Spans) ────────────────────────────────────
-- Primary query: By trace_id + service
CREATE TABLE IF NOT EXISTS omniwatch.traces
(
    trace_id        String,
    span_id         String,
    parent_span_id  Nullable(String),
    service_name    String,
    operation_name  String,
    entity_id       String,
    entity_type     LowCardinality(String),
    duration_ms     Float64,
    status_code     LowCardinality(String),
    status_message  String,
    attributes      Map(String, String),
    start_time      DateTime64(3, 'UTC'),
    end_time        DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(start_time)
ORDER BY (trace_id, service_name, start_time)
SETTINGS index_granularity = 8192;

-- ─── Anomalies ──────────────────────────────────────────────────────
-- Primary query: By status + timestamp
CREATE TABLE IF NOT EXISTS omniwatch.anomalies
(
    anomaly_id      String,
    entity_id       String,
    entity_type     LowCardinality(String),
    entity_layer    UInt8,
    metric_name     String,
    anomaly_score   Float64,
    confidence      UInt8,
    deviation_from_baseline String,
    status          LowCardinality(String) DEFAULT 'open',
    topology_context String,
    created_at      DateTime64(3, 'UTC'),
    resolved_at     Nullable(DateTime64(3, 'UTC'))
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (status, created_at)
SETTINGS index_granularity = 8192;

-- ─── Incidents ──────────────────────────────────────────────────────
-- Primary query: By severity + status
CREATE TABLE IF NOT EXISTS omniwatch.incidents
(
    incident_id     String,
    severity        LowCardinality(String),
    business_impact_score UInt8,
    root_cause      String,
    related_anomaly_ids Array(String),
    deduplicated_count UInt32 DEFAULT 1,
    sla_breach_risk LowCardinality(String),
    assigned_to     String,
    status          LowCardinality(String) DEFAULT 'open',
    created_at      DateTime64(3, 'UTC'),
    updated_at      DateTime64(3, 'UTC'),
    resolved_at     Nullable(DateTime64(3, 'UTC'))
)
ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(created_at)
ORDER BY (incident_id)
SETTINGS index_granularity = 8192;

-- ─── Profiles (Continuous Profiling) ────────────────────────────────
-- Primary query: By entity_id + time
CREATE TABLE IF NOT EXISTS omniwatch.profiles
(
    profile_id      String,
    entity_id       String,
    entity_type     LowCardinality(String),
    profile_type    LowCardinality(String),
    duration_ms     Float64,
    cpu_usage_pct   Float64,
    memory_bytes    UInt64,
    allocations     UInt64,
    sample_data     String,
    timestamp       DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (entity_id, profile_type, timestamp)
SETTINGS index_granularity = 8192;

-- ─── Pending Approvals ──────────────────────────────────────────────
-- Primary query: By status = 'pending'
CREATE TABLE IF NOT EXISTS omniwatch.pending_approvals
(
    approval_id     String,
    action_type     String,
    entity_id       String,
    proposed_action String,
    risk_score      Float64,
    incident_id     Nullable(String),
    requested_by    String,
    status          LowCardinality(String) DEFAULT 'pending',
    created_at      DateTime64(3, 'UTC'),
    expires_at      DateTime64(3, 'UTC'),
    approved_at     Nullable(DateTime64(3, 'UTC')),
    approved_by     Nullable(String)
)
ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(created_at)
ORDER BY (status, approval_id)
SETTINGS index_granularity = 8192;

-- ─── Knowledge Base ─────────────────────────────────────────────────
-- Primary query: By root_cause_entity_type
CREATE TABLE IF NOT EXISTS omniwatch.knowledge_base
(
    entry_id        String,
    incident_id     String,
    root_cause_entity_id   String,
    root_cause_entity_type LowCardinality(String),
    root_cause_description String,
    resolution_actions     String,
    resolution_outcome     LowCardinality(String),
    resolution_time_seconds UInt32,
    confidence      Float64,
    created_at      DateTime64(3, 'UTC'),
    updated_at      DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(created_at)
ORDER BY (root_cause_entity_type, entry_id)
SETTINGS index_granularity = 8192;

-- ─── Simulations ────────────────────────────────────────────────────
-- Primary query: By simulation_id + mode
CREATE TABLE IF NOT EXISTS omniwatch.simulations
(
    simulation_id   String,
    mode            LowCardinality(String),
    proposed_action String,
    predicted_outcome String,
    resolution_confidence Float64,
    recovery_time_minutes Float64,
    side_effects    Array(String),
    revenue_recovery_usd  Float64,
    risk_score      Float64,
    recommendation  LowCardinality(String),
    incident_id     Nullable(String),
    created_at      DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(created_at)
PARTITION BY toYYYYMM(created_at)
ORDER BY (simulation_id)
SETTINGS index_granularity = 8192;

-- ─── Config Drifts ──────────────────────────────────────────────────
-- Primary query: By drift_source + status
CREATE TABLE IF NOT EXISTS omniwatch.config_drifts
(
    drift_id        String,
    drift_source    LowCardinality(String),
    detection_method LowCardinality(String),
    drifted_entity  String,
    expected_state  String,
    actual_state    String,
    remediation_tool LowCardinality(String),
    remediation_action String,
    confidence      Float64,
    status          LowCardinality(String) DEFAULT 'detected',
    created_at      DateTime64(3, 'UTC'),
    remediated_at   Nullable(DateTime64(3, 'UTC'))
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (drift_source, status, created_at)
SETTINGS index_granularity = 8192;

-- ─── Cost & Carbon ──────────────────────────────────────────────────
-- Primary query: By entity_id + time
CREATE TABLE IF NOT EXISTS omniwatch.cost_carbon
(
    entity_id       String,
    entity_type     LowCardinality(String),
    hourly_cost_usd Float64,
    carbon_grams_per_hour Float64,
    cloud_provider  LowCardinality(String),
    region          LowCardinality(String),
    cost_center_id  Nullable(String),
    timestamp       DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (entity_id, timestamp)
SETTINGS index_granularity = 8192;

-- ─── Audit Log (Append-Only) ───────────────────────────────────────
-- Primary query: By event_type + user_id + timestamp
-- Retention: 7 years (configurable via AUDIT_LOG_RETENTION_YEARS)
CREATE TABLE IF NOT EXISTS omniwatch.audit_log
(
    event_id        String DEFAULT generateUUIDv4(),
    event_type      LowCardinality(String),
    user_id         String,
    resource_type   LowCardinality(String),
    resource_id     String,
    action          LowCardinality(String),
    outcome         LowCardinality(String),
    metadata        String DEFAULT '{}',
    ip_address      String DEFAULT '',
    timestamp       DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (event_type, user_id, timestamp)
TTL timestamp + INTERVAL 7 YEAR
SETTINGS index_granularity = 8192;
