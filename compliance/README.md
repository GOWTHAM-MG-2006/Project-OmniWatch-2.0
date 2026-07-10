# Compliance

Enterprise compliance evidence generation for OmniWatch 2.0.

## Components

### AuditLogger (`audit_logger.py`)
- Append-only audit logger backed by ClickHouse
- Logs API calls, remediation actions, config changes, login/logout, policy evaluations
- Provides `query_events()` and `get_stats()` for evidence retrieval

### SOC2Reporter (`soc2_reporter.py`)
- Generates SOC2 Type II evidence packages
- Maps OmniWatch actions to Trust Service Criteria (CC6.1–CC8.1)
- Outputs Markdown report with control assessment and evidence snapshots

### ISO27001Reporter (`iso27001_reporter.py`)
- Generates ISO 27001 Annex A evidence packages
- Maps OmniWatch actions to Annex A controls (A.9.1–A.16.1)
- Outputs Markdown report with control mapping, evidence snapshots, risk assessment, and treatment plan

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

## Running Tests

```bash
python -m pytest tests/test_compliance/ -v
```
