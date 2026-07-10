# Continuous Learning Layer (Layer 10)

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

## Technology

- Scikit-Learn (recommendation engine)
- PyTorch (pattern mining)
- ClickHouse (incident storage)
- MinIO (ML datasets)
