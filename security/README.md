# Security Layer (Layer 9: SentinelPlane)

## Runtime Security & Compliance

- **runtime_security.py** — eBPF LSM hooks (privilege, escape, RCE detection)
- **vulnerability_manager.py** — SBOM (Syft) + CVE correlation (Grype) + reachability
- **cspm_checker.py** — Cloud Security Posture Management (Checkov)
- **perf_sec_correlator.py** — Performance-security correlation

## Detection Capabilities

- Brute force attacks
- Privilege escalation
- Container escape attempts
- Remote code execution
- CVE reachability analysis
- Cloud misconfigurations

## Technology

- eBPF LSM hooks (runtime security)
- Grype (vulnerability scanning)
- Syft (SBOM generation)
- Checkov (CSPM)
