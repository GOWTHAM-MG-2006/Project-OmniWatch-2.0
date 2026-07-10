# Security Layer (Layer 9: SentinelPlane)

## Runtime Security & Compliance

SentinelPlane provides runtime security monitoring, vulnerability management, and cloud security posture management integrated with the OmniWatch AI engine.

## Components

### Runtime Security
- **runtime_security.py** — eBPF LSM hooks for real-time threat detection
  - Privilege escalation attempts
  - Container escape attempts
  - Remote code execution (RCE)
  - Brute force attacks
  - File system integrity violations

### Vulnerability Management
- **vulnerability_manager.py** — SBOM + CVE correlation + reachability analysis
  - Syft: Software Bill of Materials (SBOM) generation
  - Grype: CVE vulnerability scanning
  - Reachability analysis: Determines if vulnerabilities are exploitable
  - Prioritization: Risk-based CVE prioritization

### Cloud Security Posture
- **cspm_checker.py** — Cloud Security Posture Management
  - Checkov: Infrastructure-as-code scanning
  - Misconfiguration detection (AWS, Azure, GCP)
  - Compliance checking (SOC2, ISO27001, GDPR)
  - Remediation recommendations

### Performance-Security Correlation
- **perf_sec_correlator.py** — Correlates security events with performance anomalies
  - Identifies security incidents causing performance degradation
  - Cross-references with NeuroEngine anomaly signals
  - Feeds into RootCauseObject evidence chain

## Detection Capabilities

| Attack Type | Detection Method | Response |
|-------------|-----------------|----------|
| Brute Force | Auth log pattern matching | IP block recommendation |
| Privilege Escalation | eBPF LSM hooks | Process termination |
| Container Escape | eBPF syscall monitoring | Alert + isolation |
| RCE | eBPF file/network monitoring | Alert + forensics |
| CVE Exploitation | SBOM + reachability | Patch recommendation |
| Cloud Misconfig | Checkov scanning | Auto-remediation via Config Drift |

## Integration Points

```
Layer 2 GhostCollector → Security telemetry → SentinelPlane
Layer 6 NeuroEngine ← SecurityAnomalySignal ← SentinelPlane
Layer 7 AutoHeal ← Remediation actions ← SentinelPlane
Cross-Cutting Config Drift ← Cloud misconfigurations ← CSPM
```

## Data Contracts

### SecurityAnomalySignal (Output)

```json
{
  "attack_type": "BRUTE_FORCE",
  "entity_id": "auth-service",
  "severity": "HIGH",
  "confidence": 0.92,
  "evidence_logs": ["Failed login from 10.0.0.5 x 50 in 60s"],
  "recommended_action": "BLOCK_IP",
  "source_ip": "10.0.0.5",
  "timestamp": "2026-07-03T08:15:00Z"
}
```

## Technology

- eBPF LSM hooks (runtime security, <1% overhead)
- Grype (vulnerability scanning)
- Syft (SBOM generation)
- Checkov (CSPM, IaC scanning)
- Microsoft Presidio (PII detection integration)

## Security vs Performance Correlation

SentinelPlane uniquely correlates security events with performance anomalies:

1. Security event detected (e.g., brute force attack)
2. NeuroEngine detects performance anomaly (e.g., CPU spike)
3. PerfSecCorrelator identifies causal link
4. RootCauseObject includes both security and performance evidence
5. AutoHeal can remediate both aspects simultaneously
