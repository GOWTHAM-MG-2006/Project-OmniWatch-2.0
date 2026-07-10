"""
OmniWatch 2.0 — NeuroEngine
Component: Causal Graph Traversal
Layer: 6
Phase: 2
Purpose: GNN + Granger causality + backward BFS DAG walker for root cause identification
Inputs: AnomalySignal + TopoBrain dependency graph
Outputs: Ranked root causes with causal scores
"""

import logging
from typing import Any
from collections import deque

import numpy as np

logger = logging.getLogger(__name__)

# Try importing statsmodels for Granger causality; graceful fallback if missing
try:
    from statsmodels.tsa.stattools import grangercausalitytests
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    logger.info("statsmodels not installed — Granger causality disabled")


# ---------------------------------------------------------------------------
# Mock dependency graph (for testing without Kuzu)
# ---------------------------------------------------------------------------

MOCK_DEPENDENCIES: dict[str, list[dict[str, Any]]] = {
    "payment-service-api": [
        {"id": "postgres-payments-primary", "name": "postgres-payments-primary", "type": "Database", "rel_type": "CALLS"},
        {"id": "redis-cache", "name": "redis-cache", "type": "Infrastructure", "rel_type": "CALLS"},
    ],
    "checkout-service": [
        {"id": "payment-service-api", "name": "payment-service-api", "type": "Service", "rel_type": "CALLS"},
    ],
    "postgres-payments-primary": [
        {"id": "payments-db-host", "name": "payments-db-host", "type": "Host", "rel_type": "HOSTED_BY"},
    ],
    "payments-db-host": [
        {"id": "payments-vpc", "name": "payments-vpc", "type": "Infrastructure", "rel_type": "HOSTED_BY"},
    ],
    "redis-cache": [],
    "payments-vpc": [],
}


# ---------------------------------------------------------------------------
# Causal Graph Traversal
# ---------------------------------------------------------------------------

class CausalGraphTraversal:
    """Backward BFS DAG walker with optional Granger causality enhancement.

    Traverses the TopoBrain dependency graph backward from anomalous entities
    to identify root causes. Optionally strengthens causal scores using
    Granger causality tests on paired time-series metrics.
    """

    def __init__(
        self,
        max_depth: int = 5,
        use_granger: bool = True,
        granger_lag: int = 5,
        min_granger_p: float = 0.05,
    ):
        self.max_depth = max_depth
        self.use_granger = use_granger and HAS_STATSMODELS
        self.granger_lag = granger_lag
        self.min_granger_p = min_granger_p

    # -- Graph access ---------------------------------------------------------

    def _get_upstream_entities(self, entity_id: str) -> list[dict[str, Any]]:
        """Get upstream dependencies for an entity.

        Queries TopoBrain (Kuzu) when available; falls back to mock data.
        Returns list of dicts with at least 'id' and 'type' keys.
        """
        # Try real Kuzu graph first
        try:
            from topology.graph_database import TopoBrainGraph
            graph = TopoBrainGraph()
            dependencies = graph.get_dependencies(entity_id)
            if dependencies:
                return dependencies
        except Exception as exc:
            logger.debug("Kuzu not available, using mock graph: %s", exc)

        # Fall back to mock dependencies
        return self._mock_upstream(entity_id)

    def _mock_upstream(self, entity_id: str) -> list[dict[str, Any]]:
        """Return mock upstream dependencies for testing."""
        return MOCK_DEPENDENCIES.get(entity_id, [])

    # -- Granger causality ----------------------------------------------------

    def compute_granger_causality(
        self,
        cause_series: list[float],
        effect_series: list[float],
        lag: int | None = None,
    ) -> dict[str, Any]:
        """Compute Granger causality between two time series.

        Tests whether *cause_series* Granger-causes *effect_series*.

        Returns
        -------
        dict with keys: p_value, f_stat, is_causal, lag
        """
        lag = lag or self.granger_lag

        if not HAS_STATSMODELS:
            return {"p_value": 1.0, "f_stat": 0.0, "is_causal": False, "lag": lag, "error": "statsmodels unavailable"}

        arr_cause = np.array(cause_series, dtype=np.float64)
        arr_effect = np.array(effect_series, dtype=np.float64)

        if len(arr_cause) < lag + 5 or len(arr_effect) < lag + 5:
            return {"p_value": 1.0, "f_stat": 0.0, "is_causal": False, "lag": lag, "error": "insufficient data"}

        # Stack: effect (col 0) as dependent, cause (col 1) as regressor
        data = np.column_stack([arr_effect, arr_cause])

        try:
            result = grangercausalitytests(data, maxlag=lag, verbose=False)
            # Pick the lag with the smallest p-value
            best_p = 1.0
            best_f = 0.0
            best_lag = lag
            for lag_val in range(1, lag + 1):
                tests = result[lag_val][0]
                p = tests["ssr_ftest"][1]
                f = tests["ssr_ftest"][0]
                if p < best_p:
                    best_p = p
                    best_f = f
                    best_lag = lag_val

            return {
                "p_value": round(float(best_p), 6),
                "f_stat": round(float(best_f), 4),
                "is_causal": best_p < self.min_granger_p,
                "lag": best_lag,
            }
        except Exception as exc:
            logger.warning("Granger test failed: %s", exc)
            return {"p_value": 1.0, "f_stat": 0.0, "is_causal": False, "lag": lag, "error": str(exc)}

    # -- BFS traversal --------------------------------------------------------

    def backward_bfs(
        self,
        start_entity_id: str,
        anomaly_map: dict[str, dict[str, Any]],
        max_depth: int | None = None,
    ) -> list[dict[str, Any]]:
        """BFS backward from *start_entity_id* through the dependency graph.

        Parameters
        ----------
        start_entity_id:
            The anomalous entity to start traversal from.
        anomaly_map:
            Mapping of entity_id → anomaly signal dict (score, severity, etc.).
        max_depth:
            Maximum traversal depth. Defaults to self.max_depth.

        Returns
        -------
        List of candidate root-cause dicts discovered during BFS.
        """
        depth_limit = max_depth or self.max_depth
        visited: set[str] = set()
        candidates: list[dict[str, Any]] = []

        queue: deque[tuple[str, list[str], int]] = deque()
        queue.append((start_entity_id, [start_entity_id], 0))

        while queue:
            current_id, path, depth = queue.popleft()

            if current_id in visited or depth > depth_limit:
                continue
            visited.add(current_id)

            # Gather upstream entities
            upstream = self._get_upstream_entities(current_id)

            for upstream_entity in upstream:
                uid = upstream_entity.get("id", "")
                if not uid or uid in visited:
                    continue

                new_path = path + [uid]
                upstream_anomaly = anomaly_map.get(uid, {})

                # Base causal score: inversely proportional to depth, boosted by upstream anomaly
                depth_penalty = 1.0 / (1.0 + depth)
                upstream_score = upstream_anomaly.get("anomaly_score", 0.0)
                base_score = depth_penalty * 0.6 + upstream_score * 0.4

                candidate = {
                    "entity_id": uid,
                    "entity_type": upstream_entity.get("type", "unknown"),
                    "depth": depth + 1,
                    "causal_score": round(base_score, 4),
                    "path": new_path,
                    "has_anomaly": uid in anomaly_map,
                    "anomaly_score": upstream_score,
                    "rel_type": upstream_entity.get("rel_type", "DEPENDS_ON"),
                }
                candidates.append(candidate)

                # Continue BFS if upstream also has anomaly (propagation chain)
                if uid in anomaly_map:
                    queue.append((uid, new_path, depth + 1))

        return candidates

    # -- Main entry point -----------------------------------------------------

    def identify_root_causes(
        self,
        anomaly_signals: list[dict[str, Any]],
        entity_metrics: dict[str, list[float]] | None = None,
    ) -> list[dict[str, Any]]:
        """Identify root causes from anomaly signals.

        1. Build anomaly map from signals.
        2. Run backward BFS from each anomalous entity.
        3. Optionally refine scores with Granger causality.
        4. Deduplicate and rank by causal_score descending.

        Parameters
        ----------
        anomaly_signals:
            List of AnomalySignal dicts (from AnomalyDetector).
        entity_metrics:
            Optional mapping of entity_id → time-series values for Granger.

        Returns
        -------
        Ranked list of root cause candidate dicts sorted by causal_score desc.
        """
        if not anomaly_signals:
            return []

        # Build anomaly map: entity_id → signal
        anomaly_map: dict[str, dict[str, Any]] = {}
        for signal in anomaly_signals:
            eid = signal.get("entity_id", "")
            if eid:
                # Keep the highest-scoring signal per entity
                existing = anomaly_map.get(eid)
                if existing is None or signal.get("anomaly_score", 0) > existing.get("anomaly_score", 0):
                    anomaly_map[eid] = signal

        # Run backward BFS from each anomalous entity
        all_candidates: list[dict[str, Any]] = []
        for entity_id in anomaly_map:
            candidates = self.backward_bfs(entity_id, anomaly_map)
            all_candidates.extend(candidates)

        # Deduplicate: keep highest causal_score per entity_id
        deduped: dict[str, dict[str, Any]] = {}
        for c in all_candidates:
            eid = c["entity_id"]
            if eid not in deduped or c["causal_score"] > deduped[eid]["causal_score"]:
                deduped[eid] = c

        candidates_list = list(deduped.values())

        # Optional Granger enhancement
        if self.use_granger and entity_metrics and len(candidates_list) > 0:
            candidates_list = self._enhance_with_granger(candidates_list, entity_metrics, anomaly_map)

        # Sort by causal_score descending
        candidates_list.sort(key=lambda x: x["causal_score"], reverse=True)

        return candidates_list

    # -- Granger enhancement --------------------------------------------------

    def _enhance_with_granger(
        self,
        candidates: list[dict[str, Any]],
        entity_metrics: dict[str, list[float]],
        anomaly_map: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Refine causal scores using Granger causality where metrics exist."""
        for candidate in candidates:
            path = candidate.get("path", [])
            if len(path) < 2:
                continue

            # Test Granger between consecutive entities in the path
            cause_id = path[-1]   # upstream (suspected cause)
            effect_id = path[-2]  # downstream (symptom)

            cause_metrics = entity_metrics.get(cause_id)
            effect_metrics = entity_metrics.get(effect_id)

            if cause_metrics and effect_metrics:
                granger_result = self.compute_granger_causality(cause_metrics, effect_metrics)
                candidate["granger"] = granger_result

                if granger_result.get("is_causal"):
                    # Boost score when Granger confirms causality
                    boost = (1.0 - granger_result["p_value"]) * 0.3
                    candidate["causal_score"] = round(
                        min(candidate["causal_score"] + boost, 1.0), 4
                    )
                elif granger_result.get("p_value", 1.0) > 0.5:
                    # Penalize when Granger strongly rejects causality
                    candidate["causal_score"] = round(
                        candidate["causal_score"] * 0.7, 4
                    )

        return candidates


# ---------------------------------------------------------------------------
# CausalGNN — Graph Attention Network for root cause identification
# ---------------------------------------------------------------------------

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from torch_geometric.nn import GATConv, global_mean_pool
    from torch_geometric.data import Data
    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False


class CausalGNN(nn.Module if HAS_TORCH else object):
    """Graph Attention Network for causal root cause identification.

    Uses 2-layer GAT to propagate anomaly signals through the dependency
    graph and identify the entity with highest causal influence.
    """

    def __init__(self, in_features: int = 4, hidden_features: int = 16, out_features: int = 1):
        if HAS_TORCH:
            super().__init__()
            if HAS_TORCH_GEOMETRIC:
                self.conv1 = GATConv(in_features, hidden_features, heads=4, concat=False)
                self.conv2 = GATConv(hidden_features, out_features, heads=1, concat=False)
            self.in_features = in_features
            self.out_features = out_features

    def forward(self, x, edge_index):
        if not HAS_TORCH_GEOMETRIC:
            return torch.zeros(x.shape[0], 1) if HAS_TORCH else None
        x = F.relu(self.conv1(x, edge_index))
        x = self.conv2(x, edge_index)
        return torch.sigmoid(x)

    def predict_causal_scores(
        self,
        adjacency: list[list[int]],
        anomaly_scores: list[float],
        entity_ids: list[str],
    ) -> dict[str, float]:
        """Predict causal scores using the GNN model.

        Args:
            adjacency: Adjacency list [entity_index -> list of neighbor indices].
            anomaly_scores: Anomaly score per entity.
            entity_ids: Entity ID per entity.

        Returns:
            Dict mapping entity_id to causal score (0-1).
        """
        if not HAS_TORCH or not HAS_TORCH_GEOMETRIC:
            return {}

        n = len(entity_ids)
        if n == 0:
            return {}

        # Build edge index
        edge_src, edge_dst = [], []
        for i, neighbors in enumerate(adjacency):
            for j in neighbors:
                if j < n:
                    edge_src.append(i)
                    edge_dst.append(j)

        if not edge_src:
            return {eid: 0.0 for eid in entity_ids}

        edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)
        x = torch.tensor([[s, 0.0, 0.0, 0.0] for s in anomaly_scores], dtype=torch.float)

        with torch.no_grad():
            scores = self.forward(x, edge_index)

        return {
            entity_ids[i]: round(float(scores[i].item()), 4)
            for i in range(min(n, scores.shape[0]))
        }


class CausalGNNRunner:
    """Runner that integrates GNN with existing BFS+Granger approach."""

    def __init__(self):
        self.model = CausalGNN() if HAS_TORCH else None
        self._trained = False

    def train(self, adjacency: list, anomaly_scores: list, labels: list, epochs: int = 100) -> float:
        """Train the GNN model on historical incident data.

        Args:
            adjacency: Adjacency list for the dependency graph.
            anomaly_scores: Anomaly scores per entity.
            labels: Ground truth root cause indices.
            epochs: Training epochs.

        Returns:
            Final training loss.
        """
        if not HAS_TORCH or not HAS_TORCH_GEOMETRIC or self.model is None:
            return 0.0

        # Build graph data
        n = len(anomaly_scores)
        edge_src, edge_dst = [], []
        for i, neighbors in enumerate(adjacency):
            for j in neighbors:
                if j < n:
                    edge_src.append(i)
                    edge_dst.append(j)

        if not edge_src:
            return 0.0

        edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)
        x = torch.tensor([[s, 0.0, 0.0, 0.0] for s in anomaly_scores], dtype=torch.float)
        y = torch.zeros(n, 1)
        for label in labels:
            if label < n:
                y[label] = 1.0

        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        loss_fn = nn.BCELoss()

        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            pred = self.model(x, edge_index)
            loss = loss_fn(pred, y)
            loss.backward()
            optimizer.step()

        self._trained = True
        return float(loss.item())

    def predict(
        self,
        adjacency: list,
        anomaly_scores: list,
        entity_ids: list,
    ) -> dict[str, float]:
        """Predict causal scores using trained GNN."""
        if self.model is None:
            return {}
        return self.model.predict_causal_scores(adjacency, anomaly_scores, entity_ids)

    @property
    def is_trained(self) -> bool:
        return self._trained and self.model is not None
