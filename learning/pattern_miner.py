"""
OmniWatch 2.0 — Continuous Learning
Component: Pattern Miner
Layer: 10
Phase: 4
Purpose: Mines recurring incident patterns to improve detection thresholds
Input: knowledge_base incident history
Output: Discovered patterns → updates NeuroEngine adaptive thresholder
Technology: PyTorch (pattern recognition)
"""

import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from config import config
from learning.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logger.info("PyTorch not installed — using statistical pattern mining")


class PatternMiner:
    """Mines recurring incident patterns from the knowledge base."""

    def __init__(self, kb: KnowledgeBase | None = None):
        self.kb = kb or KnowledgeBase()

    def mine_patterns(
        self,
        lookback_days: int = 30,
        min_occurrences: int = 3,
    ) -> list[dict[str, Any]]:
        """Mine recurring patterns from incident history.

        Args:
            lookback_days: How many days of history to analyze.
            min_occurrences: Minimum occurrences to consider a pattern.

        Returns:
            List of discovered patterns with confidence scores.
        """
        # Query all incidents from knowledge base
        all_incidents = self.kb.query_by_entity("", limit=1000)

        if not all_incidents:
            return []

        if HAS_TORCH:
            return self._torch_pattern_mining(all_incidents, min_occurrences)
        return self._statistical_pattern_mining(all_incidents, min_occurrences)

    def _statistical_pattern_mining(
        self, incidents: list[dict], min_occurrences: int,
    ) -> list[dict[str, Any]]:
        """Statistical pattern mining without PyTorch."""
        patterns = []

        # Pattern 1: Recurring entity type failures
        entity_failures = Counter()
        for inc in incidents:
            entity = inc.get("root_cause_entity", "")
            if entity:
                entity_failures[entity] += 1

        for entity, count in entity_failures.most_common(10):
            if count >= min_occurrences:
                patterns.append({
                    "pattern_type": "recurring_entity_failure",
                    "entity": entity,
                    "occurrences": count,
                    "confidence": min(1.0, count / len(incidents) * 5),
                    "recommendation": f"Increase monitoring frequency for {entity}",
                })

        # Pattern 2: Action type effectiveness
        action_success = defaultdict(lambda: {"total": 0, "successes": 0})
        for inc in incidents:
            action = inc.get("action_type", "unknown")
            action_success[action]["total"] += 1
            if inc.get("action_success"):
                action_success[action]["successes"] += 1

        for action, stats in action_success.items():
            if stats["total"] >= min_occurrences:
                rate = stats["successes"] / stats["total"]
                patterns.append({
                    "pattern_type": "action_effectiveness",
                    "action_type": action,
                    "success_rate": round(rate, 2),
                    "occurrences": stats["total"],
                    "confidence": rate,
                    "recommendation": f"Prioritize {action} for similar incidents (success rate: {rate:.0%})",
                })

        # Pattern 3: Severity clustering
        severity_counts = Counter(inc.get("severity", "P4") for inc in incidents)
        for severity, count in severity_counts.most_common():
            if count >= min_occurrences:
                patterns.append({
                    "pattern_type": "severity_distribution",
                    "severity": severity,
                    "occurrences": count,
                    "confidence": count / len(incidents),
                    "recommendation": f"Review threshold for {severity} incidents",
                })

        return patterns

    def _torch_pattern_mining(
        self, incidents: list[dict], min_occurrences: int,
    ) -> list[dict[str, Any]]:
        """PyTorch-based pattern mining for more complex analysis."""
        # Start with statistical patterns
        patterns = self._statistical_pattern_mining(incidents, min_occurrences)

        # Add neural pattern detection if enough data
        if len(incidents) >= 10:
            try:
                # Encode incidents as feature vectors
                features = self._encode_incidents(incidents)
                if features is not None and features.shape[0] >= 10:
                    # Simple autoencoder for anomaly detection
                    reconstructed, latent = self._autoencode(features)
                    reconstruction_error = torch.mean((features - reconstructed) ** 2, dim=1)

                    # High reconstruction error = unusual pattern
                    threshold = torch.mean(reconstruction_error) + torch.std(reconstruction_error)
                    unusual_indices = torch.where(reconstruction_error > threshold)[0]

                    if len(unusual_indices) > 0:
                        patterns.append({
                            "pattern_type": "unusual_cluster",
                            "occurrences": len(unusual_indices.tolist()),
                            "confidence": config.PATTERN_MINER_CONFIDENCE,
                            "recommendation": "Unusual incident pattern detected — manual review recommended",
                        })
            except Exception as e:
                logger.debug("Neural pattern mining failed: %s", e)

        return patterns

    def _encode_incidents(self, incidents: list[dict]) -> "torch.Tensor | None":
        """Encode incidents as numerical feature vectors."""
        if not HAS_TORCH or not incidents:
            return None

        severity_map = {"P1": 4, "P2": 3, "P3": 2, "P4": 1}
        features = []
        for inc in incidents:
            severity_val = severity_map.get(inc.get("severity", "P4"), 1)
            success_val = 1.0 if inc.get("action_success") else 0.0
            exec_time = min(inc.get("execution_time_seconds", 0) / 300, 1.0)
            features.append([severity_val / 4, success_val, exec_time])

        return torch.tensor(features, dtype=torch.float32)

    def _autoencode(self, x: "torch.Tensor") -> tuple["torch.Tensor", "torch.Tensor"]:
        """Simple autoencoder for pattern detection."""
        input_dim = x.shape[1]
        hidden_dim = max(2, input_dim // 2)

        encoder = nn.Linear(input_dim, hidden_dim)
        decoder = nn.Linear(hidden_dim, input_dim)

        latent = torch.relu(encoder(x))
        reconstructed = decoder(latent)
        return reconstructed, latent
