package omniwatch.security

default allow = false

# Block auto-remediation for CRITICAL security incidents
block_auto {
    input.severity == "CRITICAL"
    input.source == "security"
}

# Require approval for any security action
require_approval {
    input.source == "security"
}

# Allow auto-block for brute force with high confidence
allow {
    input.attack_type == "BRUTE_FORCE"
    input.confidence > 0.9
    input.action == "BLOCK_IP"
}
