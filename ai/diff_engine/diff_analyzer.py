"""OmniWatch 2.0 — NeuroEngine
Component: Diff Analyzer
Layer: 6
Phase: 2
Purpose: Cross-signal differential analysis (BubbleUp extended) comparing bad vs normal windows
Inputs: Lists of event dicts (bad_data, normal_data)
Outputs: Ranked list of attributes with differential scores"""

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


class DiffAnalyzer:
    """Honeycomb BubbleUp-style differential analysis.

    Compares attribute distributions between bad and normal data windows
    to find over-represented values that distinguish failures from healthy state.
    """

    def analyze(
        self,
        bad_data: list[dict[str, Any]],
        normal_data: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Compare bad vs normal data windows to find distinguishing attributes.

        Args:
            bad_data: List of event dicts representing the anomalous window.
            normal_data: List of event dicts representing the normal window.

        Returns:
            Ranked list of dicts with keys: attribute, score, over_represented_value,
            bad_count, normal_count, details.
        """
        if not bad_data:
            logger.warning("No bad data provided for differential analysis")
            return []
        if not normal_data:
            logger.warning("No normal data provided; using bad-data-only mode")
            normal_data = []

        bad_attrs = self._extract_attributes(bad_data)
        normal_attrs = self._extract_attributes(normal_data)

        all_keys = set(bad_attrs.keys()) | set(normal_attrs.keys())
        results: list[dict[str, Any]] = []

        for key in all_keys:
            score = self._compute_differential_score(
                key, bad_attrs, normal_attrs, len(bad_data), len(normal_data)
            )
            if score <= 0:
                continue

            over_rep = self._find_over_represented(
                key, bad_attrs.get(key, {}), normal_attrs.get(key, {})
            )

            bad_total = sum(bad_attrs.get(key, {}).values())
            normal_total = sum(normal_attrs.get(key, {}).values())

            results.append(
                {
                    "attribute": key,
                    "score": round(score, 4),
                    "over_represented_value": over_rep["value"],
                    "over_represented_count": over_rep["count"],
                    "bad_count": bad_total,
                    "normal_count": normal_total,
                    "details": over_rep.get("details", {}),
                }
            )

        results.sort(key=lambda r: r["score"], reverse=True)
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_attributes(
        self, events: list[dict[str, Any]]
    ) -> dict[str, dict[str, int]]:
        """Extract attribute value counts from a list of event dicts.

        Returns:
            {attribute_name: {value_str: count}}
        """
        attrs: dict[str, dict[str, int]] = {}
        for event in events:
            for key, value in event.items():
                val_str = str(value)
                if key not in attrs:
                    attrs[key] = {}
                attrs[key][val_str] = attrs[key].get(val_str, 0) + 1
        return attrs

    def _compute_differential_score(
        self,
        key: str,
        bad_attrs: dict[str, dict[str, int]],
        normal_attrs: dict[str, dict[str, int]],
        bad_total: int,
        normal_total: int,
    ) -> float:
        """Compute information-gain-like differential score.

        Measures how much more likely a value is in bad vs normal data,
        weighted by frequency in bad data.
        """
        bad_values = bad_attrs.get(key, {})
        normal_values = normal_attrs.get(key, {})

        if not bad_values or bad_total == 0:
            return 0.0

        score = 0.0
        for val, bad_count in bad_values.items():
            bad_freq = bad_count / bad_total
            normal_freq = normal_values.get(val, 0) / max(normal_total, 1)
            # Information gain approximation: bad_freq * log2(bad_freq / normal_freq)
            ratio = bad_freq / max(normal_freq, 0.001)
            if ratio > 1.0:
                score += bad_freq * math.log2(ratio)

        return score

    def _find_over_represented(
        self,
        key: str,
        bad_values: dict[str, int],
        normal_values: dict[str, int],
    ) -> dict[str, Any]:
        """Find the most over-represented value in bad vs normal."""
        if not bad_values:
            return {"value": None, "count": 0, "details": {}}

        bad_total = sum(bad_values.values())
        normal_total = sum(normal_values.values()) if normal_values else 0

        best_val = None
        best_ratio = 0.0
        best_count = 0

        for val, bad_count in bad_values.items():
            bad_freq = bad_count / bad_total
            normal_freq = normal_values.get(val, 0) / max(normal_total, 1)
            # Over-representation ratio
            ratio = bad_freq / max(normal_freq, 0.001)
            if ratio > best_ratio:
                best_ratio = ratio
                best_val = val
                best_count = bad_count

        return {
            "value": best_val,
            "count": best_count,
            "details": {
                "over_rep_ratio": round(best_ratio, 2),
                "bad_frequency": round(best_count / bad_total, 4) if bad_total else 0,
                "normal_frequency": round(
                    normal_values.get(best_val, 0) / max(normal_total, 1), 4
                )
                if best_val
                else 0,
            },
        }
