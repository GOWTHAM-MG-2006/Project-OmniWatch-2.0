package omniwatch.remediation

default allow = false

# Auto-remediate P1 incidents with high confidence + SimulaX validation
allow {
    input.severity == "P1"
    input.confidence > 0.95
    input.simulaX_validated == true
}

# Require approval for medium confidence P1
require_approval {
    input.severity == "P1"
    input.confidence <= 0.95
    input.confidence > 0.7
}

# Auto-remediate P2 with very high confidence
allow {
    input.severity == "P2"
    input.confidence > 0.98
}

# Block auto-remediation for P3/P4
block_auto {
    input.severity == "P3"
}

block_auto {
    input.severity == "P4"
}
