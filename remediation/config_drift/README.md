# Configuration Drift Engine (Cross-Cutting)

**Phase:** 3
**Technology:** gitpython, kubernetes client, terraform CLI, Ansible

## Components

| File | Component | Purpose |
|------|-----------|---------|
| `drift_detector.py` | Drift Detector | Detects drift across K8s, OS, Cloud, Git layers |
| `argocd_integrator.py` | ArgoCD Integrator | Routes K8s drift → ArgoCD self-heal sync |
| `ansible_integrator.py` | Ansible Integrator | Routes OS drift → Ansible EDA playbook |
| `terraform_integrator.py` | Terraform Integrator | Routes cloud drift → Terraform state reconciliation |
| `git_integrator.py` | Git Integrator | Routes Git drift → Auto-revert commit |

## Data Flow

```
DriftDetector
  → detect_git_drift() → ConfigDriftEvent (source=git) → GitIntegrator → revert
  → detect_k8s_drift() → ConfigDriftEvent (source=kubernetes) → ArgoCDIntegrator → sync
  → detect_terraform_drift() → ConfigDriftEvent (source=cloud) → TerraformIntegrator → apply
  → ConfigDriftEvent → PolicyEngine → AutoHeal
```

## Dependencies

- gitpython (Git drift detection)
- kubectl (K8s drift detection)
- terraform CLI (Cloud drift detection)
- ArgoCD API (K8s remediation)
- Ansible (OS remediation)
