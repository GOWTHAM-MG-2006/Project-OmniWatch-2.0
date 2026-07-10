# SimulaX — Layer 8: Digital Twin & Simulation

**Phase:** 3
**Technology:** SimPy, Redis, Optuna

## Components

| File | Component | Purpose |
|------|-----------|---------|
| `digital_twin.py` | Digital Twin | Continuously updated model of production environment |
| `remediation_sim.py` | Remediation Simulator | Simulates proposed fixes before execution |
| `capacity_sim.py` | Capacity Simulator | Simulates traffic growth and resource exhaustion |
| `deployment_sim.py` | Deployment Simulator | Simulates deployment rollout impact |
| `chaos_sim.py` | Chaos Simulator | Simulates failure injection and cascade propagation |
| `bayesian_calibration.py` | Bayesian Calibration | Auto-tunes simulation parameters against reality |

## Data Flow

```
NexusStore (metrics) + TopoBrain (topology) + NeuroEngine (models)
  → Digital Twin (Redis state)
    → RemediationSim (SimPy) → SimulaXResult → AutoHeal
    → CapacitySim (SimPy) → Capacity Report
    → DeploymentSim (SimPy) → Risk Score → Block/Warn/Approve
    → ChaosSim (SimPy) → Blast Radius + Resilience Gaps
    → BayesianCalibration (Optuna) → Calibrated Parameters → Redis
```

## Dependencies

- Redis (state storage)
- SimPy (discrete event simulation)
- Optuna (Bayesian optimization — optional, graceful fallback)
