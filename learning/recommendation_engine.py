"""
OmniWatch 2.0 — Continuous Learning
Component: Recommendation Engine
Layer: 10
Phase: 4
Purpose: Surfaces historically successful actions for new incidents
Input: New IncidentRecord + knowledge_base historical data
Output: Ranked list of recommended actions with success rates
Technology: Scikit-Learn (similarity matching)
"""

import logging
from typing import Any

from learning.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.info("scikit-learn not installed — using rule-based recommendations")


class RecommendationEngine:
    """Surfaces historically successful actions for new incidents using similarity matching."""

    def __init__(self, kb: KnowledgeBase | None = None):
        self.kb = kb or KnowledgeBase()

    def recommend(
        self,
        incident: dict[str, Any],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Recommend actions for a new incident based on historical data.

        Args:
            incident: New IncidentRecord dict.
            limit: Maximum number of recommendations.

        Returns:
            List of recommended actions with success rates, sorted by relevance.
        """
        severity = incident.get("severity", "P4")
        root_cause = incident.get("root_cause", "")

        # Query knowledge base for similar incidents
        historical = self.kb.query_by_entity(root_cause, limit=100)

        if not historical:
            return self._default_recommendations(severity)

        if HAS_SKLEARN:
            return self._sklearn_recommend(incident, historical, limit)
        return self._rule_recommend(incident, historical, limit)

    def _sklearn_recommend(
        self,
        incident: dict[str, Any],
        historical: list[dict[str, Any]],
        limit: int,
    ) -> list[dict[str, Any]]:
        """Use TF-IDF similarity to find matching historical incidents."""
        incident_text = self._incident_to_text(incident)
        historical_texts = [self._incident_to_text(h) for h in historical]

        try:
            vectorizer = TfidfVectorizer(max_features=100)
            all_texts = [incident_text] + historical_texts
            tfidf_matrix = vectorizer.fit_transform(all_texts)

            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

            scored = []
            for i, (sim, hist) in enumerate(zip(similarities, historical)):
                if hist.get("action_success"):
                    scored.append({
                        "action_type": hist.get("action_type", "unknown"),
                        "success_rate": 1.0,
                        "similarity": round(float(sim), 3),
                        "historical_incident_id": hist.get("incident_id", ""),
                        "execution_time": hist.get("execution_time_seconds", 0),
                    })

            scored.sort(key=lambda x: x["similarity"], reverse=True)
            return scored[:limit]
        except Exception as e:
            logger.warning("TF-IDF recommendation failed: %s", e)
            return self._rule_recommend(incident, historical, limit)

    def _rule_recommend(
        self,
        incident: dict[str, Any],
        historical: list[dict[str, Any]],
        limit: int,
    ) -> list[dict[str, Any]]:
        """Rule-based recommendation from historical successes."""
        action_stats: dict[str, dict] = {}
        for h in historical:
            action = h.get("action_type", "unknown")
            if action not in action_stats:
                action_stats[action] = {"total": 0, "successes": 0}
            action_stats[action]["total"] += 1
            if h.get("action_success"):
                action_stats[action]["successes"] += 1

        recommendations = []
        for action, stats in action_stats.items():
            if stats["successes"] > 0:
                recommendations.append({
                    "action_type": action,
                    "success_rate": round(stats["successes"] / stats["total"], 2),
                    "similarity": 0.5,
                    "total_attempts": stats["total"],
                })

        recommendations.sort(key=lambda x: x["success_rate"], reverse=True)
        return recommendations[:limit]

    def _default_recommendations(self, severity: str) -> list[dict[str, Any]]:
        """Default recommendations when no historical data exists."""
        defaults = {
            "P1": [{"action_type": "rollback", "success_rate": 0.85, "similarity": 0, "note": "default for P1"}],
            "P2": [{"action_type": "restart_pod", "success_rate": 0.80, "similarity": 0, "note": "default for P2"}],
            "P3": [{"action_type": "scale", "success_rate": 0.70, "similarity": 0, "note": "default for P3"}],
        }
        return defaults.get(severity, [{"action_type": "restart_pod", "success_rate": 0.70, "similarity": 0}])

    def _incident_to_text(self, incident: dict) -> str:
        """Convert incident to text for TF-IDF vectorization."""
        parts = [
            incident.get("severity", ""),
            incident.get("root_cause", ""),
            incident.get("root_cause", {}).get("entity_type", "") if isinstance(incident.get("root_cause"), dict) else "",
        ]
        return " ".join(str(p) for p in parts if p)
