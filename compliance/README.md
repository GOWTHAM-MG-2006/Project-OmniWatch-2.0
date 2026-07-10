# Compliance

Enterprise compliance evidence generation for OmniWatch 2.0.

## Components

### AuditLogger (`audit_logger.py`)
- Append-only audit logger backed by ClickHouse
- Logs API calls, remediation actions, config changes, login/logout, policy evaluations
- Provides `query_events()` and `get_stats()` for evidence retrieval
- 7-year retention policy (configurable via AUDIT_LOG_RETENTION_YEARS)

### SOC2Reporter (`soc2_reporter.py`)
- Generates SOC2 Type II evidence packages
- Maps OmniWatch actions to Trust Service Criteria (CC6.1–CC8.1)
- Outputs Markdown report with control assessment and evidence snapshots

### ISO27001Reporter (`iso27001_reporter.py`)
- Generates ISO 27001 Annex A evidence packages
- Maps OmniWatch actions to Annex A controls (A.9.1–A.16.1)
- Outputs Markdown report with control mapping, evidence snapshots, risk assessment, and treatment plan

## Design Decisions

### Report Generation: String Formatting vs Jinja2

The compliance reporters use Python string formatting (f-strings) rather than Jinja2 templates. This was a deliberate design choice:

**Rationale:**
1. **Simplicity**: The report structure is static — no dynamic template logic required
2. **Dependencies**: Avoids adding Jinja2 as a runtime dependency for a simple use case
3. **Maintainability**: String formatting is easier to read and modify for this specific use case
4. **Performance**: Marginally faster than template rendering (negligible for this use case)

**Trade-off acknowledged**: If report templates need to become dynamic (e.g., user-configurable sections, conditional blocks), migrating to Jinja2 would be straightforward.

## Data Flow

```
System Actions → AuditLogger.log_event() → ClickHouse audit_log
                                                    ↓
                                          AuditLogger.query_events()
                                          AuditLogger.get_stats()
                                                    ↓
                                          ┌─────────┴─────────┐
                                          ↓                   ↓
                                     SOC2Reporter      ISO27001Reporter
                                          ↓                   ↓
                                     .md report         .md report
```

## ISO 27001 Annex A Controls

| Control | Name | Evidence Source |
|---------|------|-----------------|
| A.9.1 | Access Control | login, logout events |
| A.9.2 | User Access Management | login events |
| A.9.4 | System Access Control | api_call events |
| A.12.1 | Operational Procedures | remediation_action events |
| A.12.4 | Logging and Monitoring | all event types |
| A.14.2 | Secure Development | config_change events |
| A.16.1 | Incident Management | remediation_action events |

## SOC2 Trust Service Criteria

| Criterion | Name | Evidence Source |
|-----------|------|-----------------|
| CC6.1 | Logical Access Controls | login, logout events |
| CC6.2 | Authentication Mechanisms | login events |
| CC6.3 | Access Authorization | policy_evaluation events |
| CC7.1 | System Monitoring | api_call events |
| CC7.2 | Anomaly Detection | api_call events |
| CC7.3 | Incident Response | remediation_action events |
| CC8.1 | Change Management | config_change events |

## Running Tests

```bash
python -m pytest tests/test_compliance/ -v
```
