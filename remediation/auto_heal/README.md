# AutoHeal — Layer 7: Autonomous Remediation

**Phase:** 3
**Technology:** OPA Rego, Python, httpx

## Components

| File | Component | Purpose |
|------|-----------|---------|
| `policy_engine.py` | Policy Engine | OPA Rego policy evaluation for auto vs approval decisions |
| `approval_workflow.py` | Approval Workflow | Human-in-the-loop approval for medium-confidence incidents |
| `action_library.py` | Action Library | Predefined remediation actions with parameters |
| `remediation_engine.py` | Remediation Engine | Executes actions against K8s API and cloud control planes |
| `rollback_manager.py` | Rollback Manager | Auto-generated rollback plans before execution |

## Data Flow

```
NeuroEngine (RootCauseObject + IncidentRecord)
  → PolicyEngine (OPA at localhost:8181)
    → auto-remediate → ActionLibrary → RemediationEngine → ActionResult
    → approve-required → ApprovalWorkflow → ClickHouse pending_approvals → RemediationEngine
    → reject → logged, no action
  → RollbackManager (generates plan before execution)
```

## Dependencies

- OPA (localhost:8181) for policy evaluation
- ClickHouse for pending_approvals table
- Redis (via Digital Twin) for current state
