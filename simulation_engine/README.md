# Simulation Engine (Layer 8: SimulaX)

## Digital Twin & What-If Simulation

Continuously updated production model for safe change validation:

- **digital_twin.py** — Continuously updated production model
- **remediation_sim.py** — Simulates proposed fixes (SimPy)
- **capacity_sim.py** — Simulates traffic growth
- **deployment_sim.py** — Simulates deployment rollout
- **chaos_sim.py** — Simulates failure injection
- **bayesian_calibration.py** — Auto-tunes model parameters (Optuna)

## Simulation Modes

1. **Remediation Simulation** — Validate fixes before applying
2. **Capacity Simulation** — Predict traffic growth impact
3. **Deployment Simulation** — Safe rollout validation
4. **Chaos Simulation** — Failure injection testing

## Technology

- SimPy (discrete event simulation)
- Redis (simulation state)
- Optuna (Bayesian hyperparameter calibration)
