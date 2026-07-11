"""
OmniWatch 2.0 — Integration
Component: Integration Registry
Layer: Integration
Phase: 7
Purpose: Central registry of all 25+ supported integrations with metadata
Inputs: N/A (static registry)
Outputs: Integration lookup table for discovery and validation
"""

from typing import Any

INTEGRATIONS: dict[str, dict[str, Any]] = {
    # ── Cloud Providers ──────────────────────────────────────────────
    "aws_ec2": {
        "class": "AWSEC2Integration",
        "category": "cloud",
        "config_required": ["AWS_ACCESS_KEY", "AWS_SECRET_KEY"],
    },
    "aws_eks": {
        "class": "AWSEKSIntegration",
        "category": "cloud",
        "config_required": ["AWS_ACCESS_KEY", "AWS_SECRET_KEY"],
    },
    "aws_rds": {
        "class": "AWSRDSIntegration",
        "category": "cloud",
        "config_required": ["AWS_ACCESS_KEY", "AWS_SECRET_KEY"],
    },
    "aws_lambda": {
        "class": "AWSLambdaIntegration",
        "category": "cloud",
        "config_required": ["AWS_ACCESS_KEY", "AWS_SECRET_KEY"],
    },
    "azure_vms": {
        "class": "AzureVMsIntegration",
        "category": "cloud",
        "config_required": ["AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"],
    },
    "azure_aks": {
        "class": "AzureAKSIntegration",
        "category": "cloud",
        "config_required": ["AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"],
    },
    "gcp_gke": {
        "class": "GCPGKEIntegration",
        "category": "cloud",
        "config_required": ["GCP_PROJECT_ID"],
    },
    "gcp_compute": {
        "class": "GCPComputeIntegration",
        "category": "cloud",
        "config_required": ["GCP_PROJECT_ID"],
    },

    # ── Databases ────────────────────────────────────────────────────
    "postgresql": {
        "class": "PostgreSQLIntegration",
        "category": "database",
        "config_required": ["POSTGRES_HOST"],
    },
    "mysql": {
        "class": "MySQLIntegration",
        "category": "database",
        "config_required": ["MYSQL_HOST"],
    },
    "mongodb": {
        "class": "MongoDBIntegration",
        "category": "database",
        "config_required": ["MONGO_URI"],
    },
    "redis_monitor": {
        "class": "RedisMonitorIntegration",
        "category": "database",
        "config_required": ["REDIS_HOST"],
    },
    "elasticsearch_monitor": {
        "class": "ElasticsearchMonitorIntegration",
        "category": "database",
        "config_required": ["ELASTICSEARCH_HOST"],
    },

    # ── Message Queues ───────────────────────────────────────────────
    "rabbitmq": {
        "class": "RabbitMQIntegration",
        "category": "message_queue",
        "config_required": ["RABBITMQ_HOST"],
    },
    "nats": {
        "class": "NATSIntegration",
        "category": "message_queue",
        "config_required": ["NATS_URL"],
    },
    "pulsar": {
        "class": "PulsarIntegration",
        "category": "message_queue",
        "config_required": ["PULSAR_URL"],
    },

    # ── Web Servers ──────────────────────────────────────────────────
    "nginx": {
        "class": "NginxIntegration",
        "category": "web_server",
        "config_required": ["NGINX_STATUS_URL"],
    },
    "apache": {
        "class": "ApacheIntegration",
        "category": "web_server",
        "config_required": ["APACHE_STATUS_URL"],
    },

    # ── CI/CD ────────────────────────────────────────────────────────
    "jenkins": {
        "class": "JenkinsIntegration",
        "category": "cicd",
        "config_required": ["JENKINS_URL"],
    },
    "circleci": {
        "class": "CircleCIIntegration",
        "category": "cicd",
        "config_required": ["CIRCLECI_TOKEN"],
    },

    # ── Monitoring ───────────────────────────────────────────────────
    "prometheus_export": {
        "class": "PrometheusExportIntegration",
        "category": "monitoring",
        "config_required": ["PROMETHEUS_PUSHGATEWAY_URL"],
    },
    "grafana_dashboard": {
        "class": "GrafanaDashboardIntegration",
        "category": "monitoring",
        "config_required": ["GRAFANA_URL"],
    },
    "jaeger_export": {
        "class": "JaegerExportIntegration",
        "category": "monitoring",
        "config_required": ["JAEGER_ENDPOINT"],
    },

    # ── Security ─────────────────────────────────────────────────────
    "wazuh": {
        "class": "WazuhIntegration",
        "category": "security",
        "config_required": ["WAZUH_URL"],
    },
    "suricata": {
        "class": "SuricataIntegration",
        "category": "security",
        "config_required": ["SURICATA_EVE_JSON_PATH"],
    },
}
