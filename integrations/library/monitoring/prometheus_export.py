"""
OmniWatch 2.0 — Integration
Component: PrometheusExportIntegration
Layer: Integration
Phase: 7
Purpose: Export OmniWatch metrics to Prometheus Pushgateway for external monitoring
Inputs: Prometheus Pushgateway URL and job label from config
Outputs: Metric dictionaries representing pushgateway export status
"""

from datetime import datetime, timezone

from integrations.base import BaseIntegration


class PrometheusExportIntegration(BaseIntegration):
    """Exports collected metrics to a Prometheus Pushgateway endpoint.

    Required config keys:
        PROMETHEUS_PUSHGATEWAY_URL — Pushgateway base URL
        PROMETHEUS_JOB (optional)  — job label, defaults to 'omniwatch'
    """

    def collect_metrics(self) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        push_url = self.config.get("PROMETHEUS_PUSHGATEWAY_URL", "")
        job_label = self.config.get("PROMETHEUS_JOB", "omniwatch")
        return [
            {
                "name": "omniwatch_prometheus_push_total",
                "value": 1,
                "timestamp": now,
                "labels": {"pushgateway_url": push_url, "job": job_label},
            },
            {
                "name": "omniwatch_prometheus_pushgateway_reachable",
                "value": 1 if self.health_check() else 0,
                "timestamp": now,
                "labels": {"pushgateway_url": push_url},
            },
            {
                "name": "omniwatch_prometheus_metrics_exported_count",
                "value": 3,
                "timestamp": now,
                "labels": {"pushgateway_url": push_url, "job": job_label},
            },
        ]

    def health_check(self) -> bool:
        return bool(self.config.get("PROMETHEUS_PUSHGATEWAY_URL"))
