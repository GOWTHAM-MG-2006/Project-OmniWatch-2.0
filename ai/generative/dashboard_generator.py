"""OmniWatch 2.0 — NeuroEngine
Component: Dashboard Generator
Layer: 6
Phase: 2
Purpose: Generates dashboard JSON configurations for real-time monitoring views
Inputs: Entity info + metric names or list of IncidentRecords
Outputs: Dashboard config dict with panels, layout, and refresh settings"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

PANEL_TYPES = {
    "metrics": "timeseries",
    "anomalies": "state-timeline",
    "topology": "node-graph",
    "incidents": "table",
    "logs": "logs",
    "heatmap": "heatmap",
    "gauge": "gauge",
    "stat": "stat",
}

DEFAULT_REFRESH_INTERVAL = "10s"
DEFAULT_TIME_RANGE = "1h"


class DashboardGenerator:
    """Generates dashboard JSON configurations.

    Produces dashboard configs with panels for metrics, anomalies,
    topology, and incidents. Can generate entity-specific dashboards
    or aggregate dashboards from incident records.
    """

    def generate(
        self,
        entity_id: str,
        entity_type: str,
        metrics: list[str],
        title: str | None = None,
        time_range: str = DEFAULT_TIME_RANGE,
    ) -> dict[str, Any]:
        """Generate a dashboard configuration for an entity.

        Args:
            entity_id: The entity identifier.
            entity_type: The entity type (Service, Database, Host, etc.).
            metrics: List of metric names to display.
            title: Optional dashboard title.
            time_range: Default time range (e.g., "1h", "6h", "24h").

        Returns:
            Dashboard config dict with panels, layout, and metadata.
        """
        dashboard_title = title or f"{entity_id} Dashboard"
        dashboard_id = self._make_id(entity_id, dashboard_title)

        panels = []
        row = 0

        # Metrics panels
        for i, metric in enumerate(metrics):
            col = (i % 3) * 8
            panels.append(self._metric_panel(entity_id, metric, col, row))
            if (i + 1) % 3 == 0:
                row += 1

        # Anomaly panel
        row += 1
        panels.append(self._anomaly_panel(entity_id, 0, row))

        # Topology panel (entity-centric view)
        panels.append(self._topology_panel(entity_id, entity_type, 8, row))

        # Recent incidents panel
        row += 1
        panels.append(self._incidents_panel(entity_id, 0, row, colspan=16))

        return {
            "id": dashboard_id,
            "title": dashboard_title,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "panels": panels,
            "time": {
                "from": f"now-{time_range}",
                "to": "now",
            },
            "refresh": DEFAULT_REFRESH_INTERVAL,
            "schema_version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tags": [entity_type.lower(), entity_id],
        }

    def generate_from_incidents(
        self,
        incidents: list[dict[str, Any]],
        title: str = "OmniWatch Incident Dashboard",
        time_range: str = "24h",
    ) -> dict[str, Any]:
        """Generate a dashboard from a list of incident records.

        Creates an overview dashboard showing all incidents with summary panels.

        Args:
            incidents: List of IncidentRecord dicts.
            title: Dashboard title.
            time_range: Default time range.

        Returns:
            Dashboard config dict.
        """
        dashboard_id = self._make_id("incidents", title)
        panels = []

        # Summary stats
        panels.append(self._stat_panel(
            "Total Incidents", len(incidents), 0, 0, unit="short"
        ))

        critical = sum(1 for i in incidents if i.get("severity") == "CRITICAL")
        panels.append(self._stat_panel(
            "Critical", critical, 5, 0, unit="short",
            thresholds={"critical": 1, "warning": 0}
        ))

        high = sum(1 for i in incidents if i.get("severity") == "HIGH")
        panels.append(self._stat_panel(
            "High", high, 10, 0, unit="short",
            thresholds={"warning": 1, "critical": 5}
        ))

        total_users = sum(
            i.get("root_cause", {}).get("business_impact", {}).get("affected_users", 0)
            for i in incidents
            if isinstance(i.get("root_cause"), dict)
        )
        panels.append(self._stat_panel(
            "Total Affected Users", total_users, 0, 1, unit="short"
        ))

        # Incidents table
        panels.append(self._all_incidents_table(incidents, 0, 2, colspan=16))

        # Severity distribution
        panels.append(self._severity_breakdown(incidents, 0, 3))

        # Top affected entities
        panels.append(self._top_entities(incidents, 8, 3))

        return {
            "id": dashboard_id,
            "title": title,
            "entity_id": "global",
            "entity_type": "System",
            "panels": panels,
            "time": {
                "from": f"now-{time_range}",
                "to": "now",
            },
            "refresh": "30s",
            "schema_version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tags": ["incidents", "overview", "global"],
        }

    def _make_id(self, entity_id: str, title: str) -> str:
        """Generate a deterministic dashboard ID."""
        raw = f"{entity_id}:{title}"
        return f"dash-{hashlib.sha256(raw.encode()).hexdigest()[:12]}"

    def _metric_panel(
        self, entity_id: str, metric: str, col: int, row: int, colspan: int = 8
    ) -> dict[str, Any]:
        """Create a time-series metric panel."""
        return {
            "id": f"panel-{hashlib.sha256(f'{entity_id}:{metric}'.encode()).hexdigest()[:8]}",
            "type": "timeseries",
            "title": metric,
            "gridPos": {"h": 8, "w": colspan, "x": col, "y": row},
            "targets": [
                {
                    "entity_id": entity_id,
                    "metric": metric,
                    "alias": metric,
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "drawStyle": "line",
                        "lineWidth": 2,
                        "fillOpacity": 10,
                        "gradientMode": "scheme",
                        "showPoints": "auto",
                        "pointSize": 5,
                    },
                    "unit": self._guess_unit(metric),
                },
            },
        }

    def _anomaly_panel(self, entity_id: str, col: int, row: int) -> dict[str, Any]:
        """Create an anomaly detection state timeline panel."""
        return {
            "id": f"panel-anomaly-{hashlib.sha256(entity_id.encode()).hexdigest()[:8]}",
            "type": "state-timeline",
            "title": "Anomaly Detection",
            "gridPos": {"h": 6, "w": 8, "x": col, "y": row},
            "targets": [
                {
                    "entity_id": entity_id,
                    "metric": "anomaly_score",
                    "alias": "Anomaly Score",
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "thresholds"},
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.5},
                            {"color": "orange", "value": 0.7},
                            {"color": "red", "value": 0.9},
                        ]
                    },
                    "min": 0,
                    "max": 1,
                },
            },
        }

    def _topology_panel(
        self, entity_id: str, entity_type: str, col: int, row: int
    ) -> dict[str, Any]:
        """Create a topology graph panel."""
        return {
            "id": f"panel-topo-{hashlib.sha256(entity_id.encode()).hexdigest()[:8]}",
            "type": "node-graph",
            "title": "Dependency Topology",
            "gridPos": {"h": 6, "w": 8, "x": col, "y": row},
            "targets": [
                {
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "depth": 3,
                }
            ],
            "options": {
                "layout": "force-directed",
                "showEdgeLabels": True,
                "nodeColor": "by-type",
                "nodeSize": "by-anomaly-score",
            },
        }

    def _incidents_panel(
        self, entity_id: str, col: int, row: int, colspan: int = 16
    ) -> dict[str, Any]:
        """Create an incidents table panel."""
        return {
            "id": f"panel-incidents-{hashlib.sha256(entity_id.encode()).hexdigest()[:8]}",
            "type": "table",
            "title": "Recent Incidents",
            "gridPos": {"h": 6, "w": colspan, "x": col, "y": row},
            "targets": [
                {
                    "entity_id": entity_id,
                    "query_type": "incidents",
                    "limit": 20,
                    "order": "desc",
                }
            ],
            "fieldConfig": {
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "severity"},
                        "properties": [
                            {
                                "id": "custom.cellOptions",
                                "value": {"type": "color-background"},
                            },
                            {
                                "id": "thresholds",
                                "value": {
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": "LOW"},
                                        {"color": "orange", "value": "MEDIUM"},
                                        {"color": "red", "value": "HIGH"},
                                    ]
                                },
                            },
                        ],
                    }
                ],
            },
        }

    def _stat_panel(
        self,
        title: str,
        value: Any,
        col: int,
        row: int,
        unit: str = "short",
        thresholds: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        """Create a single-stat panel."""
        panel_id = f"panel-stat-{hashlib.sha256(f'{title}:{value}'.encode()).hexdigest()[:8]}"
        config: dict[str, Any] = {
            "id": panel_id,
            "type": "stat",
            "title": title,
            "gridPos": {"h": 4, "w": 5, "x": col, "y": row},
            "targets": [{"value": value}],
            "fieldConfig": {
                "defaults": {
                    "unit": unit,
                    "thresholds": {
                        "steps": [{"color": "green", "value": None}]
                    },
                },
            },
            "options": {
                "reduceOptions": {"calcs": ["lastNotNull"]},
                "colorMode": "background",
                "graphMode": "none",
                "textMode": "auto",
            },
        }

        if thresholds:
            steps = [{"color": "green", "value": None}]
            if "warning" in thresholds:
                steps.append({"color": "yellow", "value": thresholds["warning"]})
            if "critical" in thresholds:
                steps.append({"color": "red", "value": thresholds["critical"]})
            config["fieldConfig"]["defaults"]["thresholds"]["steps"] = steps

        return config

    def _all_incidents_table(
        self,
        incidents: list[dict[str, Any]],
        col: int,
        row: int,
        colspan: int = 16,
    ) -> dict[str, Any]:
        """Create a table of all incidents."""
        rows = []
        for inc in incidents[:50]:
            rc = inc.get("root_cause", {})
            biz = rc.get("business_impact", {}) if isinstance(rc, dict) else {}
            rows.append({
                "problem_id": inc.get("problem_id", "N/A"),
                "severity": inc.get("severity", "UNKNOWN"),
                "confidence": inc.get("confidence", 0),
                "root_entity": rc.get("entity", "N/A") if isinstance(rc, dict) else "N/A",
                "affected_users": biz.get("affected_users", 0) if isinstance(biz, dict) else 0,
                "timestamp": inc.get("analysis_timestamp", "N/A"),
            })

        return {
            "id": "panel-all-incidents",
            "type": "table",
            "title": "All Incidents",
            "gridPos": {"h": 8, "w": colspan, "x": col, "y": row},
            "targets": [{"rows": rows}],
            "fieldConfig": {
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "severity"},
                        "properties": [
                            {
                                "id": "custom.cellOptions",
                                "value": {"type": "color-background"},
                            }
                        ],
                    }
                ],
            },
        }

    def _severity_breakdown(
        self, incidents: list[dict[str, Any]], col: int, row: int
    ) -> dict[str, Any]:
        """Create a severity breakdown panel."""
        counts: dict[str, int] = {}
        for inc in incidents:
            sev = inc.get("severity", "UNKNOWN")
            counts[sev] = counts.get(sev, 0) + 1

        return {
            "id": "panel-severity-breakdown",
            "type": "piechart",
            "title": "Severity Distribution",
            "gridPos": {"h": 6, "w": 8, "x": col, "y": row},
            "targets": [{"data": counts}],
            "options": {
                "legend": {"displayMode": "list", "placement": "right"},
                "pieType": "donut",
            },
        }

    def _top_entities(
        self, incidents: list[dict[str, Any]], col: int, row: int
    ) -> dict[str, Any]:
        """Create a top affected entities panel."""
        entity_counts: dict[str, int] = {}
        for inc in incidents:
            rc = inc.get("root_cause", {})
            if isinstance(rc, dict):
                entity = rc.get("entity", "unknown")
                entity_counts[entity] = entity_counts.get(entity, 0) + 1

        sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        data = {e: c for e, c in sorted_entities}

        return {
            "id": "panel-top-entities",
            "type": "barchart",
            "title": "Top Affected Entities",
            "gridPos": {"h": 6, "w": 8, "x": col, "y": row},
            "targets": [{"data": data}],
            "options": {
                "orientation": "horizontal",
                "showValue": "auto",
                "groupMode": "vertical",
            },
        }

    def _guess_unit(self, metric: str) -> str:
        """Guess the unit for a metric name."""
        metric_lower = metric.lower()
        if "latency" in metric_lower or "duration" in metric_lower or "time" in metric_lower:
            return "ms"
        if "rate" in metric_lower and "error" in metric_lower:
            return "percentunit"
        if "cpu" in metric_lower or "memory" in metric_lower or "usage" in metric_lower:
            return "percentunit"
        if "count" in metric_lower or "total" in metric_lower:
            return "short"
        if "bytes" in metric_lower or "size" in metric_lower:
            return "bytes"
        return "short"
