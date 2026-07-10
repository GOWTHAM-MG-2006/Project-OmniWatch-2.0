# Auth — OmniWatch 2.0

**Layer:** Enterprise (Phase 6)

## Components

| Component | File | Purpose |
|-----------|------|---------|
| `SSOProvider` | `sso_provider.py` | OIDC SSO with JWT access/refresh token lifecycle, Redis-backed sessions |
| `RBACManager` | `rbac_manager.py` | Role-Based Access Control with 5 predefined roles |
| `require_auth` | `middleware.py` | FastAPI `Depends` function enforcing JWT + RBAC on endpoints |

## Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access to all resources (`*:*`) |
| `sre` | Incidents (CRUD), topology (read), remediation (execute), policies (R/W), metrics/logs (read) |
| `developer` | Services/traces/metrics/incidents/logs (read only) |
| `viewer` | Dashboard/incidents/topology/services (read only) |
| `security` | Security events/vulnerabilities/CSPM/incidents (read only) |

## Middleware Usage

```python
from fastapi import FastAPI, Depends
from auth.middleware import require_auth

app = FastAPI()

@app.get("/api/v1/incidents")
async def list_incidents(user=Depends(require_auth("incidents", "read"))):
    return {"incidents": [...], "requested_by": user["user_id"]}
```

The middleware:
1. Extracts Bearer JWT from the `Authorization` header
2. Validates JWT signature and expiry via `SSOProvider.validate_token()`
3. Checks RBAC permissions via `RBACManager.has_permission()` for each role
4. Returns the authenticated user dict on success
5. Logs every access decision (success and denial) to the audit trail

**Error codes:**
- `401` — Missing token, invalid token, or expired token
- `403` — Valid token but user's roles lack the required permission

## Configuration

All configuration via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | `default-dev-secret-change-in-prod` | HMAC key for JWT signing (min 32 bytes for production) |
| `REDIS_HOST` | `localhost` | Redis host for sessions and role storage |
| `REDIS_PORT` | `6379` | Redis port |
| `CLICKHOUSE_HOST` | `clickhouse` | ClickHouse host for audit logs |
| `CLICKHOUSE_PORT` | `9000` | ClickHouse native protocol port |

## Testing

```bash
python -m pytest tests/auth/ -v
```
