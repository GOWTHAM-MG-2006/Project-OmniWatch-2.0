# Remediation Layer (Layer 7: AutoHeal)

## Autonomous Remediation Engine

5 autonomy tiers with OPA policy gates:

### AutoHeal Components
- **policy_engine.py** — OPA Rego policy evaluation
- **approval_workflow.py** — Human-in-the-loop approval
- **action_library.py** — Predefined remediation actions
- **remediation_engine.py** — Executes K8s/cloud API actions
- **rollback_manager.py** — Auto-generated rollback plans

### Configuration Drift Engine
- **drift_detector.py** — Detects drift across all layers
- **argocd_integrator.py** — K8s drift → ArgoCD self-heal
- **ansible_integrator.py** — OS drift → Ansible EDA playbook
- **terraform_integrator.py** — Cloud drift → Terraform state
- **git_integrator.py** — Git drift → Auto-revert commit

### OPA Policies
- **remediation.rego** — Auto vs approval decisions
- **security.rego** — Security action authorization
- **config_drift.rego** — Drift remediation rules

## Technology

- OPA Rego (policy evaluation)
- Go (remediation engine, action library)
- Python (workflow orchestration)
