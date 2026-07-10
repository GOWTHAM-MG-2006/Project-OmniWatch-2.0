"""
OmniWatch 2.0 — SentinelPlane
Component: PerfSecCorrelator
Layer: 9
Phase: 2
Purpose: Correlate performance anomalies with security events for unified RCA
Inputs: Performance anomaly signals, Security anomaly signals
Outputs: Correlation results → NeuroEngine (Layer 6) for combined analysis
"""

import json
from datetime import datetime, timezone
from typing import Any

CORRELATION_PATTERNS = {
    "DDOS": {
        "description": "Distributed denial of service attack",
        "perf_indicators": ["cpu_spike", "memory_spike", "network_saturation", "high_latency", "connection_timeout"],
        "sec_indicators": ["brute_force", "network_flood", "volumetric_attack"],
        "time_window_seconds": 300,
        "confidence_base": 0.85,
        "recommended_action": "RATE_LIMIT_AND_BLOCK",
    },
    "CRYPTOJACKING": {
        "description": "Unauthorized cryptocurrency mining",
        "perf_indicators": ["cpu_spike", "high_cpu_usage", "unexpected_process"],
        "sec_indicators": ["unauthorized_process", "suspicious_binary", "c2_communication"],
        "time_window_seconds": 600,
        "confidence_base": 0.80,
        "recommended_action": "KILL_PROCESS_AND_ISOLATE",
    },
    "DATA_EXFILTRATION": {
        "description": "Sensitive data being stolen",
        "perf_indicators": ["network_spike", "outbound_traffic_spike", "disk_io_spike"],
        "sec_indicators": ["data_exfiltration", "unauthorized_access", "sensitive_file_access"],
        "time_window_seconds": 300,
        "confidence_base": 0.82,
        "recommended_action": "BLOCK_EGRESS_AND_INVESTIGATE",
    },
    "CREDENTIAL_STUFFING": {
        "description": "Automated credential testing attack",
        "perf_indicators": ["high_latency", "error_rate_spike", "database_connection_spike"],
        "sec_indicators": ["brute_force", "auth_failure_spike", "multiple_failed_logins"],
        "time_window_seconds": 180,
        "confidence_base": 0.78,
        "recommended_action": "RATE_LIMIT_AUTH_AND_BLOCK_IP",
    },
}


class PerfSecCorrelator:
    def __init__(self):
        self.patterns = CORRELATION_PATTERNS

    def correlate(
        self,
        perf_events: list[dict[str, Any]],
        sec_events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        correlations = []

        for pattern_name, pattern in self.patterns.items():
            matching_perf = self._find_matching_events(
                perf_events, pattern["perf_indicators"]
            )
            matching_sec = self._find_matching_events(
                sec_events, pattern["sec_indicators"]
            )

            if matching_perf and matching_sec:
                time_aligned = self._check_time_alignment(
                    matching_perf,
                    matching_sec,
                    pattern["time_window_seconds"],
                )
                if time_aligned:
                    confidence = self._calculate_confidence(
                        pattern, matching_perf, matching_sec
                    )
                    correlations.append({
                        "correlation_type": pattern_name,
                        "description": pattern["description"],
                        "confidence": round(confidence, 2),
                        "severity": self._get_correlation_severity(confidence),
                        "matching_perf_events": len(matching_perf),
                        "matching_sec_events": len(matching_sec),
                        "time_window_seconds": pattern["time_window_seconds"],
                        "recommended_action": pattern["recommended_action"],
                        "evidence": {
                            "perf_indicators_matched": [
                                e.get("event_type") for e in matching_perf
                            ],
                            "sec_indicators_matched": [
                                e.get("event_type") for e in matching_sec
                            ],
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

        correlations.sort(key=lambda x: x["confidence"], reverse=True)
        return correlations

    def _find_matching_events(
        self,
        events: list[dict[str, Any]],
        indicators: list[str],
    ) -> list[dict[str, Any]]:
        matched = []
        for event in events:
            event_type = event.get("event_type", "").lower()
            message = event.get("message", "").lower()
            for indicator in indicators:
                if indicator.lower() in event_type or indicator.lower() in message:
                    matched.append(event)
                    break
        return matched

    def _check_time_alignment(
        self,
        perf_events: list[dict[str, Any]],
        sec_events: list[dict[str, Any]],
        window_seconds: int,
    ) -> bool:
        if not perf_events or not sec_events:
            return False

        perf_times = []
        for e in perf_events:
            ts = e.get("timestamp", "")
            if ts:
                try:
                    perf_times.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
                except ValueError:
                    continue

        sec_times = []
        for e in sec_events:
            ts = e.get("timestamp", "")
            if ts:
                try:
                    sec_times.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
                except ValueError:
                    continue

        if not perf_times or not sec_times:
            return True

        for pt in perf_times:
            for st in sec_times:
                diff = abs((pt - st).total_seconds())
                if diff <= window_seconds:
                    return True

        return False

    def _calculate_confidence(
        self,
        pattern: dict,
        matching_perf: list[dict],
        matching_sec: list[dict],
    ) -> float:
        base = pattern["confidence_base"]
        perf_bonus = min(len(matching_perf) * 0.03, 0.10)
        sec_bonus = min(len(matching_sec) * 0.03, 0.10)
        return min(base + perf_bonus + sec_bonus, 0.99)

    def _get_correlation_severity(self, confidence: float) -> str:
        if confidence >= 0.90:
            return "CRITICAL"
        elif confidence >= 0.80:
            return "HIGH"
        elif confidence >= 0.60:
            return "MEDIUM"
        return "LOW"
