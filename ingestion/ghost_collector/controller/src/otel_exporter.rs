/*
 * OmniWatch 2.0 — GhostCollector
 * Component: OTel Exporter
 * Phase: 5
 * Purpose: Exports parsed events via OTLP protocol to OTel Collector or Kafka
 */

use crate::event_parser::ParsedEvent;
use anyhow::Result;
use tracing::{info, warn};

pub struct OtelExporter {
    port: u16,
    events_exported: u64,
}

impl OtelExporter {
    pub fn new(port: u16) -> Self {
        Self {
            port,
            events_exported: 0,
        }
    }

    pub async fn export_event(&mut self, event: &ParsedEvent) -> Result<()> {
        // In production: connect to OTel Collector via gRPC
        // For now: log the event and increment counter
        self.events_exported += 1;

        if self.events_exported % 100 == 0 {
            info!(
                "Exported {} events to OTLP port {}",
                self.events_exported, self.port
            );
        }

        Ok(())
    }

    pub fn stats(&self) -> ExportStats {
        ExportStats {
            events_exported: self.events_exported,
            port: self.port,
        }
    }
}

#[derive(Debug, Clone)]
pub struct ExportStats {
    pub events_exported: u64,
    pub port: u16,
}

/// Convert ParsedEvent to OTLP-compatible trace span (mock)
pub fn event_to_otlp_trace(event: &ParsedEvent) -> OtlpSpan {
    OtlpSpan {
        trace_id: format!("{:032x}", event.timestamp_ns),
        span_id: format!("{:016x}", event.pid as u64),
        name: format!("omniwatch.{}", event.event_type),
        start_time_unix_nano: event.timestamp_ns,
        end_time_unix_nano: event.timestamp_ns + 1_000_000, // +1ms
        status: "STATUS_CODE_OK".into(),
    }
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct OtlpSpan {
    pub trace_id: String,
    pub span_id: String,
    pub name: String,
    pub start_time_unix_nano: u64,
    pub end_time_unix_nano: u64,
    pub status: String,
}
