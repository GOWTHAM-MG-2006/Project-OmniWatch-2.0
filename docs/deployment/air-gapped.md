# OmniWatch 2.0 — Air-Gapped Deployment Guide

Deploy OmniWatch in environments with no internet access (isolated networks, classified systems, edge sites).

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Source machine** | Internet-connected workstation with Docker 24.0+ and Helm 3.12+ |
| **Target machine** | Kubernetes 1.25+ cluster (or Docker 24.0+ for single-node) with no internet access |
| **Transfer medium** | USB drive, approved file transfer, or internal file share with ≥100 GB free |
| **Registry** | Private container registry on the target network (e.g., Harbor, Docker Registry, Nexus) |

## Overview

The air-gapped deployment has two phases:

1. **On the source machine** — pull all images and chart dependencies, package them for transfer
2. **On the target machine** — load images into the private registry, install via Helm or Docker Compose

## Step 1: Pull Images (Source Machine)

### Container Images

Pull and save all required images:

```bash
#!/bin/bash
# pull-images.sh — Run on the internet-connected source machine

IMAGES=(
  "confluentinc/cp-zookeeper:7.6.0"
  "confluentinc/cp-kafka:7.6.0"
  "clickhouse/clickhouse-server:24.3"
  "minio/minio:latest"
  "redis:7-alpine"
  "openpolicyagent/opa:latest"
  "ollama/ollama:latest"
  "omniwatch/dashboard-backend:latest"
  "omniwatch/dashboard-frontend:latest"
)

for img in "${IMAGES[@]}"; do
  echo "Pulling $img..."
  docker pull "$img"
done

echo "Saving images to tarball..."
docker save "${IMAGES[@]}" -o omniwatch-images.tar

echo "Done. Transfer omniwatch-images.tar to the target network."
ls -lh omniwatch-images.tar
```

### Helm Charts

```bash
# Pull the OmniWatch Helm chart
helm repo add omniwatch https://charts.omniwatch.dev
helm repo update
helm pull omniwatch/omniwatch --untar --destination ./omniwatch-chart

# Bundle the chart
tar -czf omniwatch-chart.tar.gz omniwatch-chart/
```

### Ollama Model

The Ollama model must also be transferred:

```bash
# Start Ollama and pull the model
docker run -d --name ollama-pull ollama/ollama:latest
docker exec ollama-pull ollama pull qwen2.5

# Export the model data
docker cp ollama-pull:/root/.ollama ./ollama-model-data
docker stop ollama-pull && docker rm ollama-pull

tar -czf omniwatch-ollama-model.tar.gz ollama-model-data/
```

## Step 2: Transfer to Target Network

Transfer these files to the target machine:

| File | Size (approx) | Contents |
|------|---------------|----------|
| `omniwatch-images.tar` | ~15–25 GB | All container images |
| `omniwatch-chart.tar.gz` | ~5 MB | Helm chart |
| `omniwatch-ollama-model.tar.gz` | ~4–8 GB | LLM model weights |
| `values.yaml` | <1 KB | Helm configuration |
| `.env` | <1 KB | Environment variables |

Verify file integrity with checksums:

```bash
# On source
sha256sum omniwatch-images.tar > checksums.txt
sha256sum omniwatch-chart.tar.gz >> checksums.txt
sha256sum omniwatch-ollama-model.tar.gz >> checksums.txt

# On target (after transfer)
sha256sum -c checksums.txt
```

## Step 3: Load Images into Private Registry (Target Machine)

### Option A: Push to Private Registry

```bash
#!/bin/bash
# load-to-registry.sh — Run on the target machine

REGISTRY="registry.internal:5000"  # Your private registry URL

# Load images into Docker
docker load -i omniwatch-images.tar

# Tag and push to private registry
IMAGES=(
  "confluentinc/cp-zookeeper:7.6.0"
  "confluentinc/cp-kafka:7.6.0"
  "clickhouse/clickhouse-server:24.3"
  "minio/minio:latest"
  "redis:7-alpine"
  "openpolicyagent/opa:latest"
  "ollama/ollama:latest"
  "omniwatch/dashboard-backend:latest"
  "omniwatch/dashboard-frontend:latest"
)

for img in "${IMAGES[@]}"; do
  docker tag "$img" "$REGISTRY/$img"
  docker push "$REGISTRY/$img"
  echo "Pushed: $REGISTRY/$img"
done
```

### Option B: Docker Compose with Local Images

For single-node Docker Compose deployments, skip the registry and load directly:

```bash
docker load -i omniwatch-images.tar
```

Then modify `docker-compose.yml` to remove the `build:` directives and use the pre-built images directly.

## Step 4: Install OmniWatch

### Kubernetes (Helm)

```bash
# Extract the Helm chart
tar -xzf omniwatch-chart.tar.gz

# Update values.yaml to use private registry
cat > values.yaml <<EOF
global:
  imagePullSecrets:
    - name: registry-credentials
  imageRegistry: registry.internal:5000

clickhouse:
  image:
    repository: registry.internal:5000/clickhouse/clickhouse-server
    tag: "24.3"
  replicaCount: 1
  # ... remaining config

kafka:
  image:
    repository: registry.internal:5000/confluentinc/cp-kafka
    tag: "7.6.0"
  replicaCount: 1
  # ... remaining config
EOF

# Create registry credentials (if private registry requires auth)
kubectl create secret docker-registry registry-credentials \
  --namespace omniwatch \
  --docker-server=registry.internal:5000 \
  --docker-username=robot$omniwatch \
  --docker-password=<token>

# Install
helm install omniwatch omniwatch-chart/omniwatch \
  --namespace omniwatch \
  --create-namespace \
  --values values.yaml
```

### Docker Compose (Single Node)

```bash
# Load images
docker load -i omniwatch-images.tar

# Load Ollama model
mkdir -p ollama-data
tar -xzf omniwatch-ollama-model.tar.gz
docker run -d --name ollama-load \
  -v $(pwd)/ollama-model-data:/root/.ollama \
  ollama/ollama:latest
docker stop ollama-load && docker rm ollama-load

# Start services (modify docker-compose.yml to use pre-pulled images)
docker-compose up -d
```

## Registry Mirror Configuration

If the target has a registry mirror (e.g., Harbor with proxy cache), configure Docker to use it:

### Docker Daemon

```json
// /etc/docker/daemon.json
{
  "registry-mirrors": ["https://registry.internal:5000"],
  "insecure-registries": ["registry.internal:5000"]
}
```

Then restart Docker:

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### Kubernetes (containerd)

For Kubernetes nodes using containerd:

```toml
# /etc/containerd/config.toml
[plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
  endpoint = ["https://registry.internal:5000"]

[plugins."io.containerd.grpc.v1.cri".registry.configs."registry.internal:5000".tls]
  insecure_skip_verify = true
```

```bash
sudo systemctl restart containerd
```

## Verification

After deployment, verify all services are running:

```bash
# Kubernetes
kubectl get pods -n omniwatch
kubectl get svc -n omniwatch

# Docker Compose
docker-compose ps
docker-compose logs --tail=20
```

## Updating in Air-Gapped Environments

Repeat Steps 1–4 with new image versions. When upgrading:

1. Pull new images on the source machine
2. Save to a new tarball (append to avoid overwriting the previous one)
3. Transfer and load into the registry
4. Update `values.yaml` with new image tags
5. Run `helm upgrade` or `docker-compose up -d`

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| `ImagePullBackOff` in K8s | Image not in private registry or wrong tag | Verify images with `crictl images` on the node |
| `manifest unknown` | Image tag mismatch | Re-check tag in `values.yaml` vs what was pushed |
| Ollama fails to load model | Model data not transferred | Ensure `ollama-model-data` is mounted at `/root/.ollama` |
| Helm install fails | Chart not extracted | Verify `omniwatch-chart/` exists after `tar -xzf` |
| Docker: "image not found" | Images not loaded | Run `docker load -i omniwatch-images.tar` again |

## Next Steps

- For local development, see [docker-compose.md](./docker-compose.md)
- For standard Kubernetes deployment, see [kubernetes.md](./kubernetes.md)
