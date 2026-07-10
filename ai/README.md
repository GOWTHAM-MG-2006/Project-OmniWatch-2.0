# AI Layer (Layer 6: NeuroEngine)

## Hypermodal AI Engine

Four AI modalities working together for proactive anomaly detection, causal root cause analysis, predictive forecasting, and grounded generative AI.

### Causal Analysis (Phase 2)
- **baseline_engine.py** — Holt-Winters + ARIMA baselines with adaptive learning
- **anomaly_detector.py** — Multi-signal anomaly detection across metrics, logs, traces
- **causal_graph_traversal.py** — GNN (PyTorch Geometric) + Granger causality + DAG walker for root cause inference
- **problem_assembler.py** — Groups related anomalies into ONE deduplicated Problem with topology context
- **root_cause_builder.py** — Packages RootCauseObject with evidence chain, blast radius, and business impact

### Predictive Analysis (Phase 2)
- **prophet_forecaster.py** — Seasonality-aware time-series forecasting with holiday effects
- **lstm_forecaster.py** — Non-linear pattern forecasting using PyTorch LSTM networks
- **predictive_trigger.py** — Auto-triggers AutoHeal when predictions breach SLO thresholds

### Generative AI (Phase 2)
- **grounded_llm_client.py** — Hallucination-safe LLM client using vLLM + LiteLLM (BYOM support)
- **output_validator.py** — Validates LLM output against evidence chain (hallucination detection)
- **incident_summary.py** — Generates ops engineer summaries with evidence citations
- **executive_report.py** — Generates non-technical business impact reports
- **runbook_generator.py** — Generates step-by-step remediation runbooks
- **post_incident_analyser.py** — Post-mortem report generation with timeline
- **dashboard_generator.py** — Auto-generates personalized dashboards per role

### Differential Analysis (Phase 2)
- **diff_analyzer.py** — Cross-signal BubbleUp comparison (extended Differential Analysis)
- **causal_hypothesis.py** — Ranked causal hypotheses with confidence scores
- **grounding_guard.py** — Evidence-backed output validation (prevents ungrounded claims)

## Data Contracts

| Object | Description | Source |
|--------|-------------|--------|
| AnomalySignal | Single anomaly with entity context | AnomalyDetector |
| RootCauseObject | Full RCA with evidence chain + blast radius | RootCauseBuilder |
| IncidentRecord | Deduplicated incident with business impact | ProblemAssembler |
| CausalHypothesis | Ranked root cause candidates | DiffEngine |

## Technology

- PyTorch Geometric (GNN), Prophet, LSTM, Merlion
- Scikit-Learn, statsmodels (Granger causality)
- vLLM, LiteLLM (BYOM LLM inference)
- httpx (async LLM API calls)
- numpy (time-series computation)

## Integration Points

```
Layer 3 StreamForge → omniwatch.anomalies.detected → NeuroEngine
Layer 5 TopoBrain → Entity relationships → CausalGraphTraversal
Layer 7 AutoHeal ← PredictiveTrigger ← NeuroEngine
Layer 10 Learning ← FeedbackLoop ← NeuroEngine outputs
```
