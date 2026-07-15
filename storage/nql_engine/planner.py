"""
OmniWatch 2.0 — NexusStore
Component: Query Planner
Layer: 4
Phase: 2
Purpose: Create execution plans from NQL ASTs, routing to hot/warm/cold tiers
Inputs: NQLNode AST from parser
Outputs: Execution plan dict with tier routing and steps
"""

import re
import logging
from typing import Any

from config import config

logger = logging.getLogger(__name__)


class QueryPlanner:
    """Creates execution plans from parsed NQL ASTs."""

    # Hot: < 1h, Warm: 1h–90d, Cold: > 90d
    HOT_MAX_HOURS = config.NQL_HOT_MAX_HOURS
    WARM_MAX_DAYS = config.NQL_WARM_MAX_DAYS

    def plan(self, ast: Any) -> dict[str, Any]:
        """Convert AST into an execution plan with tier routing."""
        dialect = ast.properties.get("dialect", "nql")
        time_range = self._extract_time_range(ast)
        tiers = self._route_tiers(time_range)
        steps = self._build_steps(ast, tiers)

        return {
            "dialect": dialect,
            "tiers": tiers,
            "time_range": time_range,
            "steps": steps,
            "has_join": any(c.node_type == "join" for c in ast.children),
        }

    def _extract_time_range(self, ast: Any) -> dict[str, Any]:
        """Extract time range from WITHIN clause or PromQL range."""
        for child in ast.children:
            if child.node_type == "within":
                return self._parse_duration(child.value)

        if ast.properties.get("range"):
            return self._parse_duration(ast.properties["range"])

        return {"hours": 1, "raw": "default 1h"}

    def _parse_duration(self, duration_str: str) -> dict[str, Any]:
        """Parse duration like '30m', '2h', '7d' into hours."""
        match = re.match(r"last\s+(\d+)([mhd])", duration_str)
        if not match:
            match = re.match(r"(\d+)([mhd])", duration_str)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            multiplier = {"m": 1 / 60, "h": 1, "d": 24}
            return {"hours": value * multiplier.get(unit, 1), "raw": duration_str}

        return {"hours": 1, "raw": duration_str}

    def _route_tiers(self, time_range: dict[str, Any]) -> list[str]:
        """Determine which storage tiers to query based on time range."""
        hours = time_range.get("hours", 1)
        tiers = []
        if hours <= self.HOT_MAX_HOURS:
            tiers.append("hot")
        if hours > self.HOT_MAX_HOURS:
            tiers.append("warm")
        if hours > self.WARM_MAX_DAYS * 24:
            tiers.append("cold")
        return tiers if tiers else ["warm"]

    def _build_steps(self, ast: Any, tiers: list[str]) -> list[dict[str, Any]]:
        """Build ordered execution steps from AST."""
        steps = []
        step_num = 1

        for child in ast.children:
            if child.node_type == "fetch":
                steps.append({
                    "step": step_num,
                    "action": "scan",
                    "target": child.value,
                    "tiers": tiers,
                })
                step_num += 1
            elif child.node_type == "where":
                steps.append({
                    "step": step_num,
                    "action": "filter",
                    "condition": child.value,
                })
                step_num += 1
            elif child.node_type == "join":
                steps.append({
                    "step": step_num,
                    "action": "join",
                    "target": child.value["target"],
                    "on": child.value["on"],
                })
                step_num += 1
            elif child.node_type == "return":
                steps.append({
                    "step": step_num,
                    "action": "project",
                    "fields": child.value,
                })
                step_num += 1

        return steps
