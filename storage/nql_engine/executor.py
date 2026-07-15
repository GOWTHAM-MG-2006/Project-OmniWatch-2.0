"""
OmniWatch 2.0 — NexusStore
Component: Query Executor
Layer: 4
Phase: 2
Purpose: Execute NQL plans across ClickHouse, DuckDB, and Kuzu backends
Inputs: Execution plan dict from planner
Outputs: Query results as list of dicts
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Orchestrates query execution across storage backends."""

    def __init__(self, warm_store=None, cold_engine=None, graph_store=None):
        self.warm_store = warm_store
        self.cold_engine = cold_engine
        self.graph_store = graph_store

    def execute(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute a query plan and return results."""
        dialect = plan.get("dialect", "nql")
        tiers = plan.get("tiers", [])
        steps = plan.get("steps", [])

        results = []

        for step in steps:
            action = step.get("action")

            if action == "scan":
                results = self._execute_scan(step, tiers)
            elif action == "filter":
                results = self._execute_filter(results, step)
            elif action == "join":
                results = self._execute_join(results, step)
            elif action == "project":
                results = self._execute_project(results, step)

        return results

    def _execute_scan(self, step: dict, tiers: list[str]) -> list[dict[str, Any]]:
        """Scan data from the appropriate tier(s)."""
        target = step.get("target", "")
        results = []

        for tier in tiers:
            if tier == "warm" and self.warm_store:
                try:
                    warm_results = self.warm_store.query(
                        f"SELECT * FROM {target} LIMIT 1000"
                    )
                    results.extend(warm_results)
                except Exception as e:
                    logger.warning("Warm store scan failed: %s", e)

            elif tier == "cold" and self.cold_engine:
                try:
                    cold_path = os.environ.get("NQL_COLD_STORE_PATH", "/tmp/omniwatch-cold")
                    cold_results = self.cold_engine.query_parquet(
                        f"{cold_path}/{target}",
                        f"SELECT * FROM data LIMIT 1000",
                    )
                    results.extend(cold_results)
                except Exception as e:
                    logger.warning("Cold store scan failed: %s", e)

        if not results and not self.warm_store and not self.cold_engine:
            logger.info("No backends connected — returning empty results for scan of '%s'", target)

        return results

    def _execute_filter(self, data: list[dict], step: dict) -> list[dict[str, Any]]:
        """Apply filter conditions to result set."""
        condition = step.get("condition", {})
        field_name = condition.get("field", "")
        operator = condition.get("operator", "")
        value = condition.get("value", "")

        if not field_name or not operator:
            return data

        filtered = []
        numeric_val = self._try_parse_number(value)

        for row in data:
            row_val = row.get(field_name)
            if row_val is None:
                continue
            if numeric_val is not None and self._compare(row_val, operator, numeric_val):
                filtered.append(row)
            elif numeric_val is None and self._compare_str(row_val, operator, value):
                filtered.append(row)

        return filtered

    def _execute_join(self, data: list[dict], step: dict) -> list[dict[str, Any]]:
        """Execute an in-memory JOIN with another target."""
        target = step.get("target", "")
        on_field = step.get("on", "")

        if not on_field:
            logger.warning("JOIN requires an ON field — returning data unchanged")
            return data

        try:
            right_results = self._execute_scan(target, None)
            right_index = {}
            for row in right_results:
                key = row.get(on_field)
                if key is not None:
                    right_index[key] = row

            joined = []
            for left_row in data:
                key = left_row.get(on_field)
                if key in right_index:
                    merged = {**left_row, **{f"right_{k}": v for k, v in right_index[key].items()}}
                    joined.append(merged)
            return joined
        except Exception as e:
            logger.warning("JOIN failed: %s", e)
            return data

    def _execute_project(self, data: list[dict], step: dict) -> list[dict[str, Any]]:
        """Project specified fields from results."""
        fields = step.get("fields", [])
        if not fields:
            return data
        return [{f: row.get(f) for f in fields} for row in data]

    def _try_parse_number(self, value: str) -> float | None:
        """Try to parse a numeric value from string, stripping units."""
        cleaned = value.lower().replace("ms", "").replace("mb", "").replace("gb", "").strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    def _compare(self, row_val: Any, operator: str, target: float) -> bool:
        """Compare a row value against target with the given operator."""
        try:
            val = float(row_val)
        except (ValueError, TypeError):
            return False
        ops = {
            ">": val > target, ">=": val >= target,
            "<": val < target, "<=": val <= target,
            "=": val == target, "==": val == target,
            "!=": val != target,
        }
        return ops.get(operator, False)

    def _compare_str(self, row_val: Any, operator: str, target: str) -> bool:
        """String comparison fallback."""
        s = str(row_val)
        if operator in ("=", "=="):
            return s == target
        if operator == "!=":
            return s != target
        if operator == "contains":
            return target in s
        return False
