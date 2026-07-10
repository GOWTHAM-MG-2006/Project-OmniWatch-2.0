# Remediation Layer (Layer 7: AutoHeal)

**Phase:** 3 (Implemented)

## Autonomous Remediation Engine

5 autonomy tiers with OPA policy gates:

### AutoHeal Components
- **policy_engine.py** — OPA Rego policy evaluation (localhost:8181)
- **approval_workflow.py** — Human-in-the-loop approval (ClickHouse pending_approvals)
- **action_library.py** — Predefined remediation actions with parameters
- **remediation_engine.py** — Executes K8s/cloud API actions (kubectl subprocess)
- **rollback_manager.py** — Auto-generated rollback plans before execution

### Configuration Drift Engine
- **drift_detector.py** — Detects drift across K8s, OS, Cloud, Git layers
- **argocd_integrator.py** — K8s drift → ArgoCD self-heal sync
- **ansible_integrator.py** — OS drift → Ansible EDA playbook
- **terraform_integrator.py** — Cloud drift → Terraform state reconciliation
- **git_integrator.py** — Git drift → Auto-revert commit

### OPA Policies
- **policies/remediation.rego** — Auto vs approval decisions (P1/P2/P3/P4)
- **policies/security.rego** — Security action authorization
- **policies/config_drift.rego** — Drift remediation rules

## Data Flow

```
NeuroEngine (RootCauseObject)
  → PolicyEngine (OPA) → auto/approve/reject
  → ActionLibrary → RemediationEngine → ActionResult
  → RollbackManager → rollback plan
  → Config Drift → DriftDetector → Integrators
```

## Dependencies

- OPA (localhost:8181) for policy evaluation
- ClickHouse for pending_approvals table
- Redis (via Digital Twin) for current state
- kubectl (K8s actions)
- gitpython (Git drift)
