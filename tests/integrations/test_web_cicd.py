"""
OmniWatch 2.0 — Tests
Component: Web Server and CI/CD Integration Tests
Layer: Integration
Phase: 7
Purpose: Validates Nginx, Apache, Jenkins, and CircleCI integration metric collection and health checks
"""

import pytest

from integrations.library.web_server.nginx import NginxIntegration
from integrations.library.web_server.apache import ApacheIntegration
from integrations.library.cicd.jenkins import JenkinsIntegration
from integrations.library.cicd.circleci import CircleCIIntegration


class TestNginx:
    def test_collect_metrics(self):
        integration = NginxIntegration(config={"NGINX_STATUS_URL": "http://localhost/nginx_status"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) == 5
        names = [m["name"] for m in metrics]
        assert "nginx_active_connections" in names
        assert "nginx_total_requests" in names

    def test_health_check_pass(self):
        integration = NginxIntegration(config={"NGINX_STATUS_URL": "http://localhost/nginx_status"})
        assert integration.health_check() is True

    def test_health_check_fail(self):
        integration = NginxIntegration(config={})
        assert integration.health_check() is False

    def test_metric_schema(self):
        integration = NginxIntegration(config={"NGINX_STATUS_URL": "http://localhost/nginx_status"})
        for metric in integration.collect_metrics():
            assert "name" in metric
            assert "value" in metric
            assert "timestamp" in metric
            assert "labels" in metric


class TestApache:
    def test_collect_metrics(self):
        integration = ApacheIntegration(config={"APACHE_STATUS_URL": "http://localhost/server-status"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) == 4
        names = [m["name"] for m in metrics]
        assert "apache_workers_total" in names
        assert "apache_requests_total" in names

    def test_health_check_pass(self):
        integration = ApacheIntegration(config={"APACHE_STATUS_URL": "http://localhost/server-status"})
        assert integration.health_check() is True

    def test_health_check_fail(self):
        integration = ApacheIntegration(config={})
        assert integration.health_check() is False

    def test_metric_schema(self):
        integration = ApacheIntegration(config={"APACHE_STATUS_URL": "http://localhost/server-status"})
        for metric in integration.collect_metrics():
            assert "name" in metric
            assert "value" in metric
            assert "timestamp" in metric
            assert "labels" in metric


class TestJenkins:
    def test_collect_metrics(self):
        integration = JenkinsIntegration(
            config={"JENKINS_URL": "http://localhost:8080", "JENKINS_USER": "admin"}
        )
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) == 5
        names = [m["name"] for m in metrics]
        assert "jenkins_queue_size" in names
        assert "jenkins_builds_success" in names
        assert "jenkins_agents_online" in names

    def test_health_check_pass(self):
        integration = JenkinsIntegration(
            config={"JENKINS_URL": "http://localhost:8080", "JENKINS_USER": "admin"}
        )
        assert integration.health_check() is True

    def test_health_check_fail(self):
        integration = JenkinsIntegration(config={})
        assert integration.health_check() is False

    def test_health_check_missing_user(self):
        integration = JenkinsIntegration(config={"JENKINS_URL": "http://localhost:8080"})
        assert integration.health_check() is False

    def test_metric_schema(self):
        integration = JenkinsIntegration(
            config={"JENKINS_URL": "http://localhost:8080", "JENKINS_USER": "admin"}
        )
        for metric in integration.collect_metrics():
            assert "name" in metric
            assert "value" in metric
            assert "timestamp" in metric
            assert "labels" in metric


class TestCircleCI:
    def test_collect_metrics(self):
        integration = CircleCIIntegration(
            config={"CIRCLECI_TOKEN": "test-token", "CIRCLECI_PROJECT": "my-project"}
        )
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) == 4
        names = [m["name"] for m in metrics]
        assert "circleci_pipelines_total" in names
        assert "circleci_workflows_success" in names

    def test_health_check_pass(self):
        integration = CircleCIIntegration(
            config={"CIRCLECI_TOKEN": "test-token", "CIRCLECI_PROJECT": "my-project"}
        )
        assert integration.health_check() is True

    def test_health_check_fail(self):
        integration = CircleCIIntegration(config={})
        assert integration.health_check() is False

    def test_health_check_missing_project(self):
        integration = CircleCIIntegration(config={"CIRCLECI_TOKEN": "test-token"})
        assert integration.health_check() is False

    def test_metric_schema(self):
        integration = CircleCIIntegration(
            config={"CIRCLECI_TOKEN": "test-token", "CIRCLECI_PROJECT": "my-project"}
        )
        for metric in integration.collect_metrics():
            assert "name" in metric
            assert "value" in metric
            assert "timestamp" in metric
            assert "labels" in metric
