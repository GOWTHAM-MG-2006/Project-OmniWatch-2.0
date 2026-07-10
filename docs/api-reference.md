# OmniWatch 2.0 API Reference

**Version:** 1.0.0
**Base URL (Production):** `https://api.omniwatch.io/v1`
**Base URL (Local):** `http://localhost:8000/api/v1`

---

## Authentication

### JWT Bearer Token
```
Authorization: Bearer <access_token>
```

### API Key (Service-to-Service)
```
X-API-Key: <api_key>
```

### Rate Limiting
- 1000 requests/minute per user
- Returns `429 Too Many Requests` when exceeded

---

## Endpoints

### Incidents

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/incidents` | List incidents (filterable) | Viewer+ |
| GET | `/api/v1/incidents/{id}` | Get incident details | Viewer+ |
| POST | `/api/v1/incidents` | Create incident | Admin |
| PATCH | `/api/v1/incidents/{id}` | Update incident | SRE+ |
| DELETE | `/api/v1/incidents/{id}` | Delete incident | Admin |
| GET | `/api/v1/incidents/{id}/timeline` | Get incident timeline | Viewer+ |

### Topology

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/topology/nodes` | List all nodes | Viewer+ |
| GET | `/api/v1/topology/edges` | List all edges | Viewer+ |
| GET | `/api/v1/topology/nodes/{id}` | Get node details | Viewer+ |
| GET | `/api/v1/topology/blast-radius/{id}` | Calculate blast radius | SRE+ |

### Metrics

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/metrics/query` | Query metrics (NQL) | Viewer+ |
| GET | `/api/v1/metrics/entity/{id}` | Get entity metrics | Viewer+ |

### Approvals

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/approvals` | List pending approvals | SRE+ |
| POST | `/api/v1/approvals/{id}/approve` | Approve action | SRE+ |
| POST | `/api/v1/approvals/{id}/reject` | Reject action | SRE+ |

### Knowledge Base

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/knowledge` | List knowledge entries | Viewer+ |
| GET | `/api/v1/knowledge/{id}` | Get entry details | Viewer+ |

### Simulations

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/simulations/remediation` | Run remediation sim | SRE+ |
| POST | `/api/v1/simulations/capacity` | Run capacity sim | SRE+ |
| POST | `/api/v1/simulations/deployment` | Run deployment sim | SRE+ |
| POST | `/api/v1/simulations/chaos` | Run chaos sim | SRE+ |

### Security

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/security/events` | List security events | Security |
| GET | `/api/v1/security/vulnerabilities` | List vulnerabilities | Security |
| GET | `/api/v1/security/compliance` | Get compliance score | Security |

### Config Drift

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/config-drift` | List drift events | SRE+ |
| GET | `/api/v1/config-drift/{id}` | Get drift event details | SRE+ |

### Reports

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/reports/soc2` | Generate SOC2 report | Admin |
| GET | `/api/v1/reports/iso27001` | Generate ISO27001 report | Admin |

### Audit

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/audit` | Query audit logs | Admin |
| GET | `/api/v1/audit/stats` | Get audit statistics | Admin |

### Health

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check | None |

### WebSocket

| Protocol | Endpoint | Description | Auth |
|----------|----------|-------------|------|
| WS | `/ws` | Real-time event streaming | Viewer+ |

---

## Error Responses

| Code | Description |
|------|-------------|
| 400 | Bad Request — invalid parameters |
| 401 | Unauthorized — missing or invalid token |
| 403 | Forbidden — insufficient permissions |
| 404 | Not Found — resource does not exist |
| 422 | Validation Error — request body validation failed |
| 429 | Rate Limited — too many requests |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2026-07-10T12:00:00Z"
}
```
