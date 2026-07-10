# OmniWatch 2.0 — Docker Compose Deployment Guide

Local development and testing using Docker Compose.

## Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Docker      | 24.0+   | 25.0+       |
| Docker Compose | 2.20+ | 2.24+     |
| RAM         | 16 GB   | 32 GB       |
| Disk        | 50 GB free | 100 GB free |
| CPU         | 4 cores | 8 cores     |

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/OmniWatch-2.0.git
cd OmniWatch-2.0

# Copy environment template
cp .env.example .env

# Start all services
docker-compose up -d

# Verify all containers are healthy
docker-compose ps
```

The full stack starts in approximately 2–3 minutes. Kafka and ClickHouse take the longest to become healthy.

## Service Endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| Dashboard Frontend | http://localhost:3000 | — |
| Dashboard Backend (API) | http://localhost:8000 | — |
| ClickHouse HTTP | http://localhost:8123 | default / (no password) |
| ClickHouse Native | localhost:9000 | default / (no password) |
| MinIO Console | http://localhost:9002 | minioadmin / minioadmin |
| MinIO API | http://localhost:9001 | minioadmin / minioadmin |
| Kafka | localhost:9092 | — |
| Redis | localhost:6379 | — |
| OPA | http://localhost:8181 | — |
| Ollama | http://localhost:11434 | — |
| Zookeeper | localhost:2181 | — |

## Architecture

The stack comprises 9 containers:

```
┌──────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  zookeeper ──► kafka ──► dashboard-backend                │
│                              │         │                 │
│  clickhouse ◄────────────────┘         │                 │
│  redis ◄──────────────────────────────┘                 │
│  minio ◄────────────────────────────────────┘            │
│  opa ◄───────────────────────────────────────┘           │
│  ollama                                                    │
│                                                          │
│  dashboard-frontend ──► dashboard-backend                 │
└──────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

All configuration is driven by the `.env` file. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:29092` | Kafka broker address (internal) |
| `CLICKHOUSE_HOST` | `clickhouse` | ClickHouse host (internal) |
| `CLICKHOUSE_HTTP_PORT` | `8123` | ClickHouse HTTP port |
| `REDIS_HOST` | `redis` | Redis host (internal) |
| `MINIO_ENDPOINT` | `minio:9000` | MinIO API endpoint (internal) |
| `MINIO_ROOT_USER` | `minioadmin` | MinIO admin username |
| `MINIO_ROOT_PASSWORD` | `minioadmin` | MinIO admin password |
| `OPA_ENDPOINT` | `http://opa:8181` | OPA base URL |
| `OLLAMA_ENDPOINT` | `http://ollama:11434` | Ollama inference endpoint |
| `OLLAMA_MODEL` | `qwen2.5` | Default LLM model |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key (change in prod) |
| `DASHBOARD_ENV` | `development` | Runtime environment |
| `DASHBOARD_LOG_LEVEL` | `info` | Log verbosity |

### Persistent Volumes

| Volume | Service | Purpose |
|--------|---------|---------|
| `clickhouse_data` | ClickHouse | Time-series metrics, logs, traces |
| `minio_data` | MinIO | Object storage (archive, ML datasets) |
| `redis_data` | Redis | Cache and deduplication state |
| `ollama_data` | Ollama | Downloaded LLM models |

### Pulling a Model for Ollama

After starting the stack, pull the default LLM model:

```bash
docker exec omniwatch-ollama ollama pull qwen2.5
```

## Useful Commands

```bash
# View logs for a specific service
docker-compose logs -f dashboard-backend

# Restart a single service
docker-compose restart clickhouse

# Stop all services (preserves volumes)
docker-compose down

# Stop all services and remove volumes (full reset)
docker-compose down -v

# Rebuild after code changes
docker-compose up -d --build dashboard-backend

# Scale a service (where supported)
docker-compose up -d --scale dashboard-backend=2
```

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| ClickHouse fails to start | Port 9000 or 8123 already in use | Stop the conflicting process or change ports in `docker-compose.yml` |
| Kafka broker not ready | Zookeeper slow to start | Wait 30s; check `docker-compose logs zookeeper` |
| MinIO console shows 502 | MinIO still initializing | Wait for healthcheck to pass; verify volume mounts |
| Dashboard shows "Cannot connect to API" | Backend not healthy | Run `docker-compose logs dashboard-backend` and check environment variables |
| Ollama returns 404 on model | Model not pulled yet | Run `docker exec omniwatch-ollama ollama pull qwen2.5` |
| Redis connection refused | Redis container crashed | Check `docker-compose logs redis`; verify `appendonly` volume permissions |
| Port conflict on host | Another service uses the same port | Edit `docker-compose.yml` to map to different host ports |
| Out of memory | Host has <16 GB RAM | Stop other containers or increase RAM; Ollama and ClickHouse are the heaviest consumers |

## Next Steps

- For production Kubernetes deployment, see [kubernetes.md](./kubernetes.md)
- For air-gapped environments, see [air-gapped.md](./air-gapped.md)
