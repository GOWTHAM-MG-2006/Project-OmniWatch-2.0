# OmniWatch 2.0 — Enterprise Integrations

Layer: Enterprise
Phase: 6
Purpose: Enterprise system integrations for incident management, deployment tracking, and infrastructure-as-code operations

## Overview

The integrations package provides connectors to enterprise systems used in modern cloud operations. Each integration follows a consistent pattern:

- Bearer token or basic authentication
- RESTful API calls via `requests`
- Structured logging for observability
- Error handling with `raise_for_status()`

## Integrations

### 1. ServiceNow (`servicenow.py`)

**Purpose**: CMDB and incident management integration

**Configuration**:
- `base_url`: ServiceNow instance URL (e.g., `https://instance.service-now.com`)
- `username`: ServiceNow username
- `password`: ServiceNow password

**Features**:
- `push_to_cmdb()`: Push discovered entities to CMDB as Configuration Items
- `create_incident()`: Create incidents from OmniWatch problems with severity mapping
- `sync_incidents()`: Bidirectional sync of ServiceNow incidents

**Entity Type Mapping**:
| OmniWatch Type | ServiceNow CMDB Class |
|----------------|----------------------|
| Service | cmdb_ci_service |
| Host | cmdb_ci_server |
| Database | cmdb_ci_db |
| Process | cmdb_ci_process |
| GenAIService | cmdb_ci_service |
| BusinessTransaction | cmdb_ci_service |
| CostCenter | cmdb_ci_cost_center |

### 2. GitHub (`github_integration.py`)

**Purpose**: Issue creation, deployment linking, and webhook handling

**Configuration**:
- `api_base`: GitHub API URL (e.g., `https://api.github.com`)
- `token`: Personal access token or GitHub App token
- `webhook_secret`: HMAC secret for webhook verification

**Features**:
- `create_issue()`: Auto-create issues with severity labels
- `link_deployment()`: Link commits to deployment events
- `verify_webhook()`: HMAC-SHA256 signature verification
- `receive_webhook()`: Process push, pull_request, and issues events

### 3. GitLab (`gitlab_integration.py`)

**Purpose**: Issue creation, deployment linking, and webhook handling

**Configuration**:
- `api_base`: GitLab API URL (e.g., `https://gitlab.com/api/v4`)
- `token`: Personal access token or project token
- `webhook_secret`: HMAC secret for webhook verification

**Features**:
- `create_issue()`: Auto-create issues with severity labels
- `link_deployment()`: Link commits to deployment events
- `verify_webhook()`: HMAC-SHA256 signature verification
- `receive_webhook()`: Process push, merge_request, and issue events

### 4. Terraform Cloud (`terraform_cloud.py`)

**Purpose**: Infrastructure-as-code operations for drift detection and remediation

**Configuration**:
- `base_url`: Terraform Cloud URL (e.g., `https://app.terraform.io`)
- `token`: API token with workspace run permissions

**Features**:
- `trigger_plan()`: Trigger plan runs from drift detection events
- `trigger_apply()`: Trigger apply runs after human approval
- `get_state()`: Retrieve current state for drift comparison
- `list_workspaces()`: List all workspaces in the organization

**Drift Detection Workflow**:
1. Config Drift Engine detects drift → calls `trigger_plan()`
2. OmniWatch approval workflow reviews changes → calls `trigger_apply()`
3. State comparison via `get_state()` for continuous monitoring

## Environment Variables

All integrations support configuration via environment variables:

```bash
# ServiceNow
SERVICENOW_BASE_URL=https://instance.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=secret

# GitHub
GITHUB_API_BASE=https://api.github.com
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# GitLab
GITLAB_API_BASE=https://gitlab.com/api/v4
GITLAB_TOKEN=glpat-xxxxxxxxxxxx
GITLAB_WEBHOOK_SECRET=your_webhook_secret

# Terraform Cloud
TERRAFORM_CLOUD_BASE_URL=https://app.terraform.io
TERRAFORM_CLOUD_TOKEN=your_api_token
```

## Testing

Run integration tests:

```bash
pytest tests/integrations/ -v
```

All integrations use mocked HTTP responses for testing. Tests verify:
- Correct API endpoint calls
- Response parsing and data extraction
- Error handling behavior

## Usage Example

```python
from integrations.terraform_cloud import TerraformCloudIntegration

# Initialize integration
tf = TerraformCloudIntegration(
    base_url="https://app.terraform.io",
    token="your_api_token"
)

# Trigger plan from drift detection
plan = tf.trigger_plan(workspace="payments-infra")
print(f"Plan started: {plan['id']}")

# After approval, trigger apply
apply = tf.trigger_apply(workspace="payments-infra", run_id=plan['id'])
print(f"Apply started: {apply['id']}")

# Get current state for monitoring
state = tf.get_state(workspace="payments-infra")
print(f"State serial: {state['serial']}")
```