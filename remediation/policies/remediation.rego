package omniwatch.remediation

default allow = false

# Auto-remediate P1 incidents with high confidence + SimulaX validation
allow if {
    input.severity == "P1"
    input.confidence > 0.95
    input.simulaX_validated == true
}

# Require approval for medium confidence P1
require_approval if {
    input.severity == "P1"
    input.confidence <= 0.95
    input.confidence > 0.7
}

# Auto-remediate P2 with very high confidence
allow if {
    input.severity == "P2"
    input.confidence > 0.98
}

# Block auto-remediation for P3/P4
block_auto if {
    input.severity == "P3"
}

block_auto if {
    input.severity == "P4"
}
