import pytest

from integrations.library.monitoring.prometheus_export import PrometheusExportIntegration
from integrations.library.monitoring.grafana_dashboard import GrafanaDashboardIntegration
from integrations.library.monitoring.jaeger_export import JaegerExportIntegration
from integrations.library.security.wazuh import WazuhIntegration
from integrations.library.security.suricata import SuricataIntegration


class TestPrometheusExport:
    def test_collect_metrics(self):
        integration = PrometheusExportIntegration(
            config={"PROMETHEUS_PUSHGATEWAY_URL": "http://localhost:9091"}
        )
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert all("name" in m and "value" in m and "timestamp" in m and "labels" in m for m in metrics)

    def test_health_check_pass(self):
        integration = PrometheusExportIntegration(
            config={"PROMETHEUS_PUSHGATEWAY_URL": "http://localhost:9091"}
        )
        assert integration.health_check() is True

    def test_health_check_fail(self):
        integration = PrometheusExportIntegration(config={})
        assert integration.health_check() is False


class TestGrafanaDashboard:
    def test_collect_metrics(self):
        integration = GrafanaDashboardIntegration(
            config={
                "GRAFANA_API_URL": "http://localhost:3000",
                "GRAFANA_API_KEY": "test-key",
            }
        )
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert all("name" in m and "value" in m and "timestamp" in m and "labels" in m for m in metrics)

    def test_health_check_pass(self):
        integration = GrafanaDashboardIntegration(
            config={
                "GRAFANA_API_URL": "http://localhost:3000",
                "GRAFANA_API_KEY": "test-key",
            }
        )
        assert integration.health_check() is True

    def test_health_check_fail_missing_key(self):
        integration = GrafanaDashboardIntegration(
            config={"GRAFANA_API_URL": "http://localhost:3000"}
        )
        assert integration.health_check() is False


class TestJaegerExport:
    def test_collect_metrics(self):
        integration = JaegerExportIntegration(
            config={"JAEGER_COLLECTOR_URL": "http://localhost:14268/api/traces"}
        )
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert all("name" in m and "value" in m and "timestamp" in m and "labels" in m for m in metrics)

    def test_health_check_pass(self):
        integration = JaegerExportIntegration(
            config={"JAEGER_COLLECTOR_URL": "http://localhost:14268/api/traces"}
        )
        assert integration.health_check() is True

    def test_health_check_fail(self):
        integration = JaegerExportIntegration(config={})
        assert integration.health_check() is False


class TestWazuh:
    def test_collect_metrics(self):
        integration = WazuhIntegration(
            config={
                "WAZUH_URL": "http://localhost:55000",
                "WAZUH_USER": "admin",
            }
        )
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert all("name" in m and "value" in m and "timestamp" in m and "labels" in m for m in metrics)

    def test_health_check_pass(self):
        integration = WazuhIntegration(
            config={"WAZUH_URL": "http://localhost:55000", "WAZUH_USER": "admin"}
        )
        assert integration.health_check() is True

    def test_health_check_fail_missing_user(self):
        integration = WazuhIntegration(
            config={"WAZUH_URL": "http://localhost:55000"}
        )
        assert integration.health_check() is False


class TestSuricata:
    def test_collect_metrics(self):
        integration = SuricataIntegration(
            config={"SURICATA_EVE_JSON_PATH": "/var/log/suricata/eve.json"}
        )
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert all("name" in m and "value" in m and "timestamp" in m and "labels" in m for m in metrics)

    def test_health_check_pass(self):
        integration = SuricataIntegration(
            config={"SURICATA_EVE_JSON_PATH": "/var/log/suricata/eve.json"}
        )
        assert integration.health_check() is True

    def test_health_check_fail(self):
        integration = SuricataIntegration(config={})
        assert integration.health_check() is False
