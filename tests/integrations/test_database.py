"""
OmniWatch 2.0 — Integration Library (Database)
Component: Database Integration Tests
Layer: Integration
Phase: 7
Purpose: Tests for PostgreSQL, MySQL, MongoDB, Redis, and Elasticsearch integrations
Inputs: Mock configuration dicts
Outputs: Test assertions for metric collection and health checks
"""

import pytest

from integrations.library.database.postgresql import PostgreSQLIntegration
from integrations.library.database.mysql import MySQLIntegration
from integrations.library.database.mongodb import MongoDBIntegration
from integrations.library.database.redis_monitor import RedisMonitorIntegration
from integrations.library.database.elasticsearch_monitor import ElasticsearchMonitorIntegration


class TestPostgreSQL:
    def test_collect_metrics(self):
        integration = PostgreSQLIntegration(config={"POSTGRES_HOST": "localhost"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        for m in metrics:
            assert "name" in m
            assert "value" in m
            assert "timestamp" in m
            assert "labels" in m

    def test_health_check(self):
        integration = PostgreSQLIntegration(config={"POSTGRES_HOST": "localhost"})
        assert integration.health_check() is True

    def test_health_check_missing_host(self):
        integration = PostgreSQLIntegration(config={})
        assert integration.health_check() is False


class TestMySQL:
    def test_collect_metrics(self):
        integration = MySQLIntegration(config={"MYSQL_HOST": "localhost"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        for m in metrics:
            assert "name" in m
            assert "value" in m
            assert "timestamp" in m
            assert "labels" in m

    def test_health_check(self):
        integration = MySQLIntegration(config={"MYSQL_HOST": "localhost"})
        assert integration.health_check() is True

    def test_health_check_missing_host(self):
        integration = MySQLIntegration(config={})
        assert integration.health_check() is False


class TestMongoDB:
    def test_collect_metrics(self):
        integration = MongoDBIntegration(config={"MONGO_URI": "mongodb://localhost:27017"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        for m in metrics:
            assert "name" in m
            assert "value" in m
            assert "timestamp" in m
            assert "labels" in m

    def test_health_check(self):
        integration = MongoDBIntegration(config={"MONGO_URI": "mongodb://localhost:27017"})
        assert integration.health_check() is True

    def test_health_check_missing_uri(self):
        integration = MongoDBIntegration(config={})
        assert integration.health_check() is False


class TestRedis:
    def test_collect_metrics(self):
        integration = RedisMonitorIntegration(config={"REDIS_HOST": "localhost"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        for m in metrics:
            assert "name" in m
            assert "value" in m
            assert "timestamp" in m
            assert "labels" in m

    def test_health_check(self):
        integration = RedisMonitorIntegration(config={"REDIS_HOST": "localhost"})
        assert integration.health_check() is True

    def test_health_check_missing_host(self):
        integration = RedisMonitorIntegration(config={})
        assert integration.health_check() is False


class TestElasticsearch:
    def test_collect_metrics(self):
        integration = ElasticsearchMonitorIntegration(config={"ELASTICSEARCH_HOST": "localhost"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        for m in metrics:
            assert "name" in m
            assert "value" in m
            assert "timestamp" in m
            assert "labels" in m

    def test_health_check(self):
        integration = ElasticsearchMonitorIntegration(config={"ELASTICSEARCH_HOST": "localhost"})
        assert integration.health_check() is True

    def test_health_check_missing_host(self):
        integration = ElasticsearchMonitorIntegration(config={})
        assert integration.health_check() is False
