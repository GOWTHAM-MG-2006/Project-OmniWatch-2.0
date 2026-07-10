# OmniWatch 2.0 — Kubernetes Deployment Guide

Production-grade deployment on Kubernetes using Helm charts.

## Prerequisites

| Requirement | Minimum Version |
|-------------|-----------------|
| Kubernetes  | 1.25+           |
| Helm        | 3.12+           |
| kubectl     | Matches cluster |
| Node count  | 3+ worker nodes |
| Storage class | ReadWriteOnce (e.g., gp3, local-path) |

### Node Sizing

A minimal production cluster requires 3 worker nodes with at least 16 vCPU and 64 GB RAM each. See the resource table below for per-service breakdown.

## Installation

```bash
# Add the OmniWatch Helm repository
helm repo add omniwatch https://charts.omniwatch.dev
helm repo update

# Create the namespace
kubectl create namespace omniwatch

# Install with default values
helm install omniwatch omniwatch/omniwatch \
  --namespace omniwatch \
  --values values.yaml

# Watch pods come up
kubectl get pods -n omniwatch -w
```

## Resource Requirements

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| ClickHouse | 4 | 8 | 8 GB | 16 GB |
| Kafka (x3) | 2 | 4 | 4 GB | 8 GB |
| Zookeeper (x3) | 0.5 | 1 | 1 GB | 2 GB |
| Redis | 1 | 2 | 2 GB | 4 GB |
| Dashboard Backend | 2 | 4 | 4 GB | 8 GB |
| Dashboard Frontend | 0.5 | 1 | 512 MB | 1 GB |
| MinIO (x4) | 1 | 2 | 2 GB | 4 GB |
| OPA | 0.5 | 1 | 512 MB | 1 GB |
| Ollama | 2 | 4 | 4 GB | 8 GB |
| **Total (approx)** | **~20 CPU** | | **~30 GB** | |

For a minimal deployment (single-replica Kafka/MinIO), total resources are approximately 10 CPU and 20 GB RAM.

## Configuration

### values.yaml

```yaml
global:
  namespace: omniwatch
  storageClass: gp3

clickhouse:
  replicaCount: 1
  resources:
    requests:
      cpu: "4"
      memory: 8Gi
    limits:
      cpu: "8"
      memory: 16Gi
  persistence:
    size: 100Gi

kafka:
  replicaCount: 3
  resources:
    requests:
      cpu: "2"
      memory: 4Gi
    limits:
      cpu: "4"
      memory: 8Gi
  persistence:
    size: 50Gi

redis:
  replicaCount: 1
  resources:
    requests:
      cpu: "1"
      memory: 2Gi
    limits:
      cpu: "2"
      memory: 4Gi

dashboard:
  backend:
    replicaCount: 2
    resources:
      requests:
        cpu: "2"
        memory: 4Gi
      limits:
        cpu: "4"
        memory: 8Gi
  frontend:
    replicaCount: 2
    resources:
      requests:
        cpu: "0.5"
        memory: 512Mi
      limits:
        cpu: "1"
        memory: 1Gi

minio:
  replicaCount: 1
  persistence:
    size: 200Gi

ollama:
  model: qwen2.5
  persistence:
    size: 50Gi
```

### ConfigMaps

Application configuration is injected via ConfigMaps. The Helm chart auto-generates them from `values.yaml`:

```bash
# View generated ConfigMaps
kubectl get configmaps -n omniwatch

# Edit configuration
kubectl edit configmap omniwatch-config -n omniwatch
```

### Secrets

Sensitive values (JWT key, MinIO credentials, etc.) are stored in Kubernetes Secrets:

```bash
# Create secrets manually
kubectl create secret generic omniwatch-secrets \
  --namespace omniwatch \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  --from-literal=minio-root-user=minioadmin \
  --from-literal=minio-root-password=$(openssl rand -hex 16)
```

In production, use a secrets manager (AWS Secrets Manager, HashiCorp Vault) with an External Secrets Operator or CSI driver.

### Ingress

The chart includes an optional Ingress resource. Enable it in `values.yaml`:

```yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: omniwatch.example.com
      paths:
        - path: /
          pathType: Prefix
          service: dashboard-frontend
        - path: /api
          pathType: Prefix
          service: dashboard-backend
  tls:
    - secretName: omniwatch-tls
      hosts:
        - omniwatch.example.com
```

## Monitoring

### Prometheus

The chart deploys a Prometheus instance (or integrates with an existing one) to scrape metrics from all OmniWatch services:

```bash
# Port-forward to Prometheus UI
kubectl port-forward svc/prometheus 9090:9090 -n omniwatch
```

Key metrics to monitor:

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `omniwatch_ingest_rate` | Events per second | < 100 for 5 min |
| `omniwatch_anomaly_latency_ms` | Time to detect anomaly | > 5000 ms |
| `omniwatch_rca_confidence_avg` | Average RCA confidence | < 0.7 for 15 min |
| `omniwatch_kafka_consumer_lag` | Consumer group lag | > 10000 |
| `omniwatch_clickhouse_query_ms` | Query latency p99 | > 2000 ms |

### Grafana

Dashboards are pre-provisioned:

```bash
# Access Grafana
kubectl port-forward svc/grafana 3001:3000 -n omniwatch
```

Default login: `admin` / `admin` (change on first login).

Pre-built dashboards:
- **OmniWatch Overview** — system health, ingest rate, error rate
- **Kafka Deep Dive** — broker metrics, consumer lag, partition distribution
- **ClickHouse Performance** — query throughput, merge activity, replication lag

### Alertmanager

Alertmanager is configured with default receivers. Update the Helm values to route alerts to your Slack, PagerDuty, or email:

```yaml
alertmanager:
  config:
    receivers:
      - name: slack
        slack_configs:
          - api_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
            channel: "#omniwatch-alerts"
    route:
      receiver: slack
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
```

## Scaling

### Horizontal Scaling

Scale stateless components (dashboard backend/frontend) independently:

```bash
# Scale backend to 5 replicas
kubectl scale deployment omniwatch-dashboard-backend \
  --replicas=5 -n omniwatch

# Scale frontend to 3 replicas
kubectl scale deployment omniwatch-dashboard-frontend \
  --replicas=3 -n omniwatch
```

### Scaling Kafka

Kafka partition count must be increased before adding brokers:

```bash
# Add partitions to a topic
kubectl exec -it omniwatch-kafka-0 -n omniwatch -- \
  kafka-topics --bootstrap-server localhost:9092 \
  --alter --topic omniwatch.telemetry.raw --partitions 12
```

Then update `kafka.replicaCount` in `values.yaml` and run:

```bash
helm upgrade omniwatch omniwatch/omniwatch \
  --namespace omniwatch \
  --values values.yaml
```

### Scaling ClickHouse

For read-heavy workloads, add read replicas:

```yaml
clickhouse:
  replicaCount: 3
  shardCount: 2
```

## Upgrades

```bash
# Update Helm repo
helm repo update

# Upgrade to latest
helm upgrade omniwatch omniwatch/omniwatch \
  --namespace omniwatch \
  --values values.yaml

# Check rollout status
kubectl rollout status deployment/omniwatch-dashboard-backend -n omniwatch
```

## Uninstall

```bash
helm uninstall omniwatch --namespace omniwatch

# Optionally remove persistent volumes
kubectl delete pvc --all -n omniwatch
kubectl delete namespace omniwatch
```

## Next Steps

- For air-gapped environments, see [air-gapped.md](./air-gapped.md)
- For local development, see [docker-compose.md](./docker-compose.md)
