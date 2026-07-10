# Continuous Learning Layer (Layer 10)

**Phase:** 4 (Implemented)

## Knowledge Base & Pattern Mining

- **knowledge_base.py** — Persistent incident outcome store (ClickHouse + MinIO)
- **feedback_loop.py** — Writes resolution outcomes to knowledge base
- **recommendation_engine.py** — Surfaces historically successful actions (Scikit-Learn)
- **pattern_miner.py** — Mines recurring incident patterns (PyTorch)

## Learning Loop

```
Incident Resolution → Feedback Loop → Knowledge Base
    → Pattern Mining → Recommendation Engine
    → Better future decisions
```

## Data Flow

```
AutoHeal (ActionResult) → FeedbackLoop → KnowledgeBase (ClickHouse)
  → PatternMiner → patterns → BaselineEngine (NeuroEngine)
  → PatternMiner → patterns → AdaptiveIntelligence (StreamForge)
  → RecommendationEngine → ranked actions → AutoHeal
```

## Integration Points

- **NeuroEngine** (`baseline_engine.py`): Receives pattern feedback to improve baselines
- **StreamForge** (`adaptive_intelligence.py`): Receives pattern feedback to adjust sampling
- **AutoHeal** (`policy_engine.py`): Queries recommendation engine for action suggestions

## Technology

- Scikit-Learn (recommendation engine — TF-IDF similarity)
- PyTorch (pattern mining — autoencoder for anomaly detection)
- ClickHouse (incident storage)
- MinIO (ML datasets)
