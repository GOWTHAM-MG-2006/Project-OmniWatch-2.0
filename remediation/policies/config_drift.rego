package omniwatch.config_drift

default allow = false

# Auto-remediate K8s drift via ArgoCD
allow if {
    input.drift_source == "kubernetes"
    input.confidence > 0.9
    input.remediation_tool == "argocd"
}

# Auto-remediate Git drift
allow if {
    input.drift_source == "git"
    input.confidence > 0.95
}

# Require approval for OS drift
require_approval if {
    input.drift_source == "os"
}

# Require approval for cloud drift (Terraform)
require_approval if {
    input.drift_source == "cloud"
}

# Block auto-remediation for low confidence
block_auto if {
    input.confidence <= 0.7
}
