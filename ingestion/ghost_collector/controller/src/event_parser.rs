/*
 * OmniWatch 2.0 — GhostCollector
 * Component: Event Parser
 * Phase: 5
 * Purpose: Parses raw eBPF events into structured telemetry objects
 */

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParsedEvent {
    pub event_type: String,
    pub timestamp_ns: u64,
    pub pid: u32,
    pub comm: String,
    pub data: EventData,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EventData {
    HttpTrace(HttpTraceData),
    Syscall(SyscallData),
    NetworkFlow(NetworkFlowData),
    Security(SecurityData),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HttpTraceData {
    pub bytes_sent: u64,
    pub bytes_received: u64,
    pub direction: u32,
    pub latency_ms: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyscallData {
    pub syscall_nr: u64,
    pub latency_ns: u64,
    pub ret: i64,
    pub fd: u64,
    pub filename: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkFlowData {
    pub src_ip: u32,
    pub dst_ip: u32,
    pub src_port: u16,
    pub dst_port: u16,
    pub proto: u8,
    pub bytes: u64,
    pub packets: u64,
    pub event_type: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityData {
    pub event_type: u32,
    pub severity: u32,
    pub detail: String,
}

/// Parse raw eBPF event bytes into structured ParsedEvent
pub fn parse_event(event_type: &str, raw_data: &[u8]) -> Option<ParsedEvent> {
    match event_type {
        "http_trace" => parse_http_trace(raw_data),
        "syscall" => parse_syscall(raw_data),
        "network_flow" => parse_network_flow(raw_data),
        "security" => parse_security(raw_data),
        _ => None,
    }
}

fn parse_http_trace(raw: &[u8]) -> Option<ParsedEvent> {
    if raw.len() < 48 {
        return None;
    }
    Some(ParsedEvent {
        event_type: "http_trace".into(),
        timestamp_ns: u64::from_le_bytes(raw[0..8].try_into().ok()?),
        pid: u32::from_le_bytes(raw[8..12].try_into().ok()?),
        comm: String::from_utf8_lossy(&raw[12..28]).trim_end_matches('\0').into(),
        data: EventData::HttpTrace(HttpTraceData {
            bytes_sent: u64::from_le_bytes(raw[28..36].try_into().ok()?),
            bytes_received: u64::from_le_bytes(raw[36..44].try_into().ok()?),
            direction: u32::from_le_bytes(raw[44..48].try_into().ok()?),
            latency_ms: 0.0,
        }),
    })
}

fn parse_syscall(raw: &[u8]) -> Option<ParsedEvent> {
    if raw.len() < 64 {
        return None;
    }
    Some(ParsedEvent {
        event_type: "syscall".into(),
        timestamp_ns: u64::from_le_bytes(raw[0..8].try_into().ok()?),
        pid: u32::from_le_bytes(raw[8..12].try_into().ok()?),
        comm: String::from_utf8_lossy(&raw[12..28]).trim_end_matches('\0').into(),
        data: EventData::Syscall(SyscallData {
            syscall_nr: u64::from_le_bytes(raw[28..36].try_into().ok()?),
            latency_ns: u64::from_le_bytes(raw[36..44].try_into().ok()?),
            ret: i64::from_le_bytes(raw[44..52].try_into().ok()?),
            fd: u64::from_le_bytes(raw[52..60].try_into().ok()?),
            filename: String::new(),
        }),
    })
}

fn parse_network_flow(raw: &[u8]) -> Option<ParsedEvent> {
    if raw.len() < 40 {
        return None;
    }
    Some(ParsedEvent {
        event_type: "network_flow".into(),
        timestamp_ns: u64::from_le_bytes(raw[0..8].try_into().ok()?),
        pid: 0,
        comm: String::new(),
        data: EventData::NetworkFlow(NetworkFlowData {
            src_ip: u32::from_le_bytes(raw[8..12].try_into().ok()?),
            dst_ip: u32::from_le_bytes(raw[12..16].try_into().ok()?),
            src_port: u16::from_le_bytes(raw[16..18].try_into().ok()?),
            dst_port: u16::from_le_bytes(raw[18..20].try_into().ok()?),
            proto: raw[20],
            bytes: u64::from_le_bytes(raw[24..32].try_into().ok()?),
            packets: u64::from_le_bytes(raw[32..40].try_into().ok()?),
            event_type: 0,
        }),
    })
}

fn parse_security(raw: &[u8]) -> Option<ParsedEvent> {
    if raw.len() < 48 {
        return None;
    }
    Some(ParsedEvent {
        event_type: "security".into(),
        timestamp_ns: u64::from_le_bytes(raw[0..8].try_into().ok()?),
        pid: u32::from_le_bytes(raw[8..12].try_into().ok()?),
        comm: String::from_utf8_lossy(&raw[12..28]).trim_end_matches('\0').into(),
        data: EventData::Security(SecurityData {
            event_type: u32::from_le_bytes(raw[28..32].try_into().ok()?),
            severity: u32::from_le_bytes(raw[32..36].try_into().ok()?),
            detail: String::new(),
        }),
    })
}

/// Generate a sample event for dry-run testing
pub fn parse_sample_event(i: u32) -> ParsedEvent {
    ParsedEvent {
        event_type: "http_trace".into(),
        timestamp_ns: std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos() as u64,
        pid: 1000 + i,
        comm: format!("test-{}", i),
        data: EventData::HttpTrace(HttpTraceData {
            bytes_sent: 1024 * i as u64,
            bytes_received: 2048 * i as u64,
            direction: 0,
            latency_ms: (i as f64) * 1.5,
        }),
    }
}
