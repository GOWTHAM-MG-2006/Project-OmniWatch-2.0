# OmniWatch 2.0 — Integration Library

Layer: Integration
Phase: 7
Purpose: 25+ pre-built integrations for cloud, database, message queue, web server, CI/CD, monitoring, and security systems

## Overview

The Integration Library provides connectors to external systems, enabling OmniWatch to collect metrics, events, and health data from your entire infrastructure.

## Architecture

```
integrations/
├── base.py                 # BaseIntegration abstract class
├── registry.py             # Integration registry and discovery
└── library/
    ├── cloud/              # AWS, Azure, GCP integrations (8)
    ├── database/           # PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch (5)
    ├── message_queue/      # RabbitMQ, NATS, Pulsar (3)
    ├── web_server/         # Nginx, Apache (2)
    ├── cicd/               # Jenkins, CircleCI (2)
    ├── monitoring/         # Prometheus, Grafana, Jaeger exports (3)
    └── security/           # Wazuh, Suricata (2)
```

## Available Integrations

### Cloud Providers (8)

| Integration | Category | Metrics Collected |
|-------------|----------|-------------------|
| `aws_ec2` | Cloud | CPU, network, disk, status checks |
| `aws_eks` | Cloud | Cluster health, node count, pod metrics |
| `aws_rds` | Cloud | CPU, connections, replication lag |
| `aws_lambda` | Cloud | Invocations, duration, errors |
| `azure_vms` | Cloud | CPU, memory, disk, network |
| `azure_aks` | Cloud | Cluster health, node count |
| `gcp_gke` | Cloud | Cluster health, node count |
| `gcp_compute` | Cloud | CPU, disk, network |

### Databases (5)

| Integration | Category | Metrics Collected |
|-------------|----------|-------------------|
| `postgresql` | Database | Connections, queries, replication, locks |
| `mysql` | Database | Connections, queries, InnoDB metrics |
| `mongodb` | Database | Connections, operations, oplog lag |
| `redis_monitor` | Database | Memory, hit rate, connections, keys |
| `elasticsearch_monitor` | Database | Cluster health, JVM, query rates |

### Message Queues (3)

| Integration | Category | Metrics Collected |
|-------------|----------|-------------------|
| `rabbitmq` | Message Queue | Queue depth, messages, consumers |
| `nats` | Message Queue | Connections, messages, subscriptions |
| `pulsar` | Message Queue | Topics, throughput, consumers |

### Web Servers (2)

| Integration | Category | Metrics Collected |
|-------------|----------|-------------------|
| `nginx` | Web Server | Connections, requests, workers |
| `apache` | Web Server | Workers, requests, errors |

### CI/CD (2)

| Integration | Category | Metrics Collected |
|-------------|----------|-------------------|
| `jenkins` | CI/CD | Queue, builds, agents, duration |
| `circleci` | CI/CD | Pipelines, workflows, duration |

### Monitoring Exports (3)

| Integration | Category | Purpose |
|-------------|----------|---------|
| `prometheus_export` | Monitoring | Export metrics to Prometheus |
| `grafana_dashboard` | Monitoring | Auto-generate dashboards |
| `jaeger_export` | Monitoring | Export traces to Jaeger |

### Security (2)

| Integration | Category | Metrics Collected |
|-------------|----------|-------------------|
| `wazuh` | Security | Alerts, critical events, agents |
| `suricata` | Security | Events, alerts, flows |

**Total: 25 integrations**

## Usage

### Basic Usage

```python
from integrations.registry import INTEGRATIONS, get_integration_class

# List all available integrations
for name, config in INTEGRATIONS.items():
    print(f"{name}: {config['category']}")

# Get integration class
cls = get_integration_class("aws_ec2")
if cls:
    integration = cls(config={
        "AWS_ACCESS_KEY": "your-key",
        "AWS_SECRET_KEY": "your-secret",
        "AWS_REGION": "us-east-1"
    })
    
    # Collect metrics
    metrics = integration.collect_metrics()
    
    # Health check
    if integration.health_check():
        print("Integration is healthy")
```

## Adding New Integrations

1. Create a new file in the appropriate category directory
2. Extend `BaseIntegration`
3. Implement `collect_metrics()` and `health_check()`
4. Add entry to `integrations/registry.py`
5. Add tests in `tests/integrations/`

```python
from integrations.base import BaseIntegration

class MyIntegration(BaseIntegration):
    def collect_metrics(self):
        return [{"name": "my_metric", "value": 42, "timestamp": "...", "labels": {}}]
    
    def health_check(self):
        return True
```

## Testing

Run all integration tests:

```bash
pytest tests/integrations/ -v
```

All integrations use mock data when external APIs are unavailable.
