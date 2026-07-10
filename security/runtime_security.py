"""
OmniWatch 2.0 — SentinelPlane
Component: RuntimeSecurityDetector
Layer: 9
Phase: 2
Purpose: Detect runtime security attacks via eBPF LSM hooks and pattern matching
Inputs: Security events (process_create, network_outbound, file_access, etc.)
Outputs: SecurityAnomalySignal → NeuroEngine (Layer 6) for security-aware RCA
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

ATTACK_PATTERNS = {
    "PRIVILEGE_ESCALATION": {
        "description": "Attempt to gain elevated privileges",
        "severity": "CRITICAL",
        "confidence_base": 0.85,
        "indicators": [
            r"sudo\s+chmod\s+777",
            r"setuid",
            r"capsh\s+--print",
            r"mount\s+.*exec",
            r"/etc/passwd.*write",
            r"/etc/shadow.*write",
            r"chmod\s+[0-7]*7[0-7]*\s+/etc/",
        ],
    },
    "CONTAINER_ESCAPE": {
        "description": "Attempt to escape container isolation",
        "severity": "CRITICAL",
        "confidence_base": 0.90,
        "indicators": [
            r"nsenter.*--target.*1",
            r"mount\s+/proc/1/ns",
            r"chroot\s+/",
            r"cgroup.*release_agent",
            r"docker\s+run.*--privileged",
            r"cap_add.*ALL",
            r"/proc/self/root",
        ],
    },
    "REMOTE_CODE_EXECUTION": {
        "description": "Remote code execution attempt",
        "severity": "CRITICAL",
        "confidence_base": 0.88,
        "indicators": [
            r"curl\s+.*\|\s*(ba)?sh",
            r"wget\s+.*\|\s*(ba)?sh",
            r"eval\s*\(",
            r"exec\s*\(",
            r"python.*-c.*import\s+os",
            r"perl.*-e",
            r"ruby.*-e",
            r"nc\s+-e",
            r"ncat\s+.*-e",
        ],
    },
    "C2_COMMUNICATION": {
        "description": "Command and control communication detected",
        "severity": "HIGH",
        "confidence_base": 0.82,
        "indicators": [
            r"curl\s+http://evil",
            r"curl\s+http://malware",
            r"beacon",
            r"keepalive.*443",
            r"reverse.*shell",
            r"bash\s+-i\s+.*>/dev/tcp",
            r"mkfifo.*nc\s+",
        ],
    },
    "DATA_EXFILTRATION": {
        "description": "Sensitive data being exfiltrated",
        "severity": "HIGH",
        "confidence_base": 0.80,
        "indicators": [
            r"curl.*-d.*@/etc/",
            r"scp\s+.*@",
            r"rsync\s+.*@",
            r"/etc/passwd.*curl",
            r"/etc/shadow.*curl",
            r"tar\s+.*\|.*curl",
            r"base64.*curl",
            r"dd\s+if=/dev/sd",
        ],
    },
    "BRUTE_FORCE": {
        "description": "Credential brute force attack",
        "severity": "MEDIUM",
        "confidence_base": 0.78,
        "indicators": [
            r"Failed password.*\d+ times",
            r"Failed login.*\d+ in \d+s",
            r"authentication failure",
            r"invalid user.*\d+ times",
            r"too many authentication failures",
            r"Account locked",
        ],
    },
}

ACTION_MAP = {
    "PRIVILEGE_ESCALATION": "ISOLATE_CONTAINER",
    "CONTAINER_ESCAPE": "ISOLATE_HOST",
    "REMOTE_CODE_EXECUTION": "KILL_PROCESS",
    "C2_COMMUNICATION": "BLOCK_IP",
    "DATA_EXFILTRATION": "BLOCK_EGRESS",
    "BRUTE_FORCE": "BLOCK_IP",
}


class RuntimeSecurityDetector:
    def __init__(self):
        self.patterns = ATTACK_PATTERNS

    def detect(self, event: dict[str, Any]) -> dict[str, Any] | None:
        message = event.get("message", "")
        entity_id = event.get("entity_id", "unknown")
        source_ip = event.get("source_ip", "0.0.0.0")

        best_match = None
        best_confidence = 0.0

        for attack_type, pattern in self.patterns.items():
            for indicator in pattern["indicators"]:
                if re.search(indicator, message, re.IGNORECASE):
                    confidence = pattern["confidence_base"]
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = attack_type
                    break

        if not best_match:
            return None

        pattern = self.patterns[best_match]
        recommended = self._recommend_action(best_match)

        return {
            "attack_type": best_match,
            "entity_id": entity_id,
            "severity": pattern["severity"],
            "confidence": round(best_confidence, 2),
            "evidence_logs": [message],
            "recommended_action": recommended,
            "source_ip": source_ip,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def detect_batch(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        signals = []
        for event in events:
            signal = self.detect(event)
            if signal:
                signals.append(signal)
        return signals

    def _recommend_action(self, attack_type: str) -> str:
        return ACTION_MAP.get(attack_type, "LOG_AND_ALERT")
