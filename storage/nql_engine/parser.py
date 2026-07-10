"""
OmniWatch 2.0 — NexusStore
Component: NQL Parser
Layer: 4
Phase: 2
Purpose: Parse NQL, PromQL, and LogQL queries into a unified AST
Inputs: Query string in any supported dialect
Outputs: NQLNode AST
"""

import re
import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class NQLNode:
    """AST node for parsed queries."""
    node_type: str
    value: Any = None
    children: list = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)


class NQLParser:
    """Parses NQL, PromQL, and LogQL into a unified AST."""

    def parse(self, query: str) -> NQLNode:
        """Detect dialect and parse into AST."""
        query = query.strip()

        if self._is_promql(query):
            return self._parse_promql(query)
        if self._is_logql(query):
            return self._parse_logql(query)
        return self._parse_nql(query)

    def _is_promql(self, query: str) -> bool:
        promql_funcs = ["rate", "irate", "increase", "histogram_quantile",
                        "sum", "avg", "min", "max", "count", "topk", "bottomk"]
        return any(query.startswith(f + "(") for f in promql_funcs)

    def _is_logql(self, query: str) -> bool:
        return query.startswith("{")

    def _parse_nql(self, query: str) -> NQLNode:
        """Parse NQL: FETCH <target> [WHERE ...] [WITHIN ...] [JOIN ...] [RETURN ...]"""
        root = NQLNode(node_type="root", properties={"dialect": "nql"})

        # FETCH clause
        fetch_match = re.match(r"FETCH\s+(\w+)", query, re.IGNORECASE)
        if fetch_match:
            root.children.append(NQLNode(
                node_type="fetch",
                value=fetch_match.group(1),
            ))

        # WHERE clause
        where_match = re.search(r"WHERE\s+(.+?)(?=\s+(?:WITHIN|JOIN|RETURN|$))", query, re.IGNORECASE)
        if where_match:
            conditions = self._parse_where(where_match.group(1))
            root.children.append(NQLNode(node_type="where", value=conditions))

        # WITHIN clause (time range)
        within_match = re.search(r"WITHIN\s+(.+?)(?=\s+(?:JOIN|RETURN|$))", query, re.IGNORECASE)
        if within_match:
            root.children.append(NQLNode(
                node_type="within",
                value=within_match.group(1).strip(),
            ))

        # JOIN clause
        join_match = re.search(r"JOIN\s+(\w+)\s+ON\s+(.+?)(?=\s+(?:RETURN|$))", query, re.IGNORECASE)
        if join_match:
            root.children.append(NQLNode(
                node_type="join",
                value={"target": join_match.group(1), "on": join_match.group(2).strip()},
            ))

        # RETURN clause
        return_match = re.search(r"RETURN\s+(.+)$", query, re.IGNORECASE)
        if return_match:
            fields = [f.strip() for f in return_match.group(1).split(",")]
            root.children.append(NQLNode(node_type="return", value=fields))

        return root

    def _parse_where(self, where_str: str) -> dict[str, Any]:
        """Parse WHERE condition like 'p99_latency > 500ms'."""
        cond_match = re.match(r"(\w+)\s*([><=!]+)\s*(.+)", where_str.strip())
        if cond_match:
            return {
                "field": cond_match.group(1),
                "operator": cond_match.group(2),
                "value": cond_match.group(3).strip(),
            }
        return {"raw": where_str.strip()}

    def _parse_promql(self, query: str) -> NQLNode:
        """Parse PromQL expressions like rate(http_requests_total{service="checkout"}[5m])."""
        func_match = re.match(r"(\w+)\((.+)\)$", query)
        if not func_match:
            return NQLNode(node_type="promql_raw", value=query,
                           properties={"dialect": "promql"})

        func_name = func_match.group(1)
        inner = func_match.group(2)

        # Extract metric name and labels: metric_name{label="val",...}
        metric_match = re.match(r'(\w+)\{([^}]*)\}\[(\w+)\]', inner)
        if metric_match:
            metric_name = metric_match.group(1)
            labels_str = metric_match.group(2)
            range_val = metric_match.group(3)
            labels = dict(re.findall(r'(\w+)="([^"]*)"', labels_str))
        else:
            metric_name = inner
            labels = {}
            range_val = ""

        return NQLNode(
            node_type="promql",
            value=func_name,
            properties={
                "dialect": "promql",
                "metric": metric_name,
                "labels": labels,
                "range": range_val,
            },
        )

    def _parse_logql(self, query: str) -> NQLNode:
        """Parse LogQL expressions like {job="api"} |= "error"."""
        label_match = re.match(r'\{([^}]*)\}', query)
        labels = {}
        if label_match:
            labels = dict(re.findall(r'(\w+)="([^"]*)"', label_match.group(1)))

        filter_match = re.search(r'\|=\s*"([^"]*)"', query)
        filter_val = filter_match.group(1) if filter_match else ""

        return NQLNode(
            node_type="logql",
            value=filter_val,
            properties={
                "dialect": "logql",
                "labels": labels,
                "filter": filter_val,
            },
        )
