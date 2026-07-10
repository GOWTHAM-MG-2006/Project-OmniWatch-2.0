# AI Layer (Layer 6: NeuroEngine)

## Hypermodal AI Engine

Four AI modalities working together:

### Causal Analysis
- **baseline_engine.py** — Holt-Winters + ARIMA baselines
- **anomaly_detector.py** — Multi-signal anomaly detection
- **causal_graph_traversal.py** — GNN (PyTorch Geometric) + Granger + DAG walker
- **problem_assembler.py** — Groups anomalies → ONE Problem
- **root_cause_builder.py** — Packages RootCauseObject

### Predictive Analysis
- **prophet_forecaster.py** — Seasonality-aware forecasting
- **lstm_forecaster.py** — Non-linear pattern forecasting (PyTorch)
- **predictive_trigger.py** — Auto-triggers AutoHeal

### Generative AI
- **grounded_llm_client.py** — Hallucination-safe LLM client (vLLM + LiteLLM)
- **output_validator.py** — Validates LLM output against input
- **incident_summary.py** — Generates ops engineer summaries
- **executive_report.py** — Generates non-technical reports
- **runbook_generator.py** — Generates step-by-step runbooks
- **post_incident_analyser.py** — Post-mortem report generation
- **dashboard_generator.py** — Auto-generates dashboards

### Differential Analysis
- **diff_analyzer.py** — Cross-signal comparison (BubbleUp extended)
- **causal_hypothesis.py** — Ranked causal hypotheses
- **grounding_guard.py** — Evidence-backed output validation

## Technology

- PyTorch Geometric (GNN), Prophet, LSTM, Merlion
- Scikit-Learn, statsmodels (Granger causality)
- vLLM, LiteLLM (BYOM LLM inference)
