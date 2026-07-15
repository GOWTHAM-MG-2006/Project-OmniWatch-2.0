"""
OmniWatch 2.0 — NexusUX
Component: FastAPI Backend
Layer: 11
Phase: 1
Purpose: API gateway for dashboard frontend
Inputs: HTTP/WS requests from React frontend
Outputs: REST responses and WebSocket events
"""

import os
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import config
from dashboard.backend.routes import (
    incidents, topology, metrics, approvals,
    knowledge, simulations, security, config_drift, reports,
    audit, auth_routes, policies,
)
from dashboard.backend.websocket import ConnectionManager
from dashboard.backend.ws_auth import verify_ws_token
from auth.middleware import require_auth  # noqa: F401 — exported for route modules

# Configure structured JSON logging
logging.basicConfig(
    level=os.getenv("DASHBOARD_LOG_LEVEL", "info").upper(),
    format='{"time":"%(asctime)s","level":"%(levelname)s","component":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OmniWatch 2.0 API",
    description="NexusUX Dashboard Backend — AIOps Platform API Gateway",
    version="1.0.0",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global Exception Handlers ──────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return structured JSON for HTTP errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all: log and return 500 for unhandled exceptions."""
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


# WebSocket connection manager
ws_manager = ConnectionManager()

# Include route modules
app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["incidents"])
app.include_router(topology.router, prefix="/api/v1/topology", tags=["topology"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["approvals"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(simulations.router, prefix="/api/v1/simulations", tags=["simulations"])
app.include_router(security.router, prefix="/api/v1/security", tags=["security"])
app.include_router(config_drift.router, prefix="/api/v1/config-drift", tags=["config-drift"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(policies.router, prefix="/api/v1/policies", tags=["policies"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "omniwatch-dashboard-backend",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/status")
async def system_status():
    """System status overview."""
    return {
        "platform": "OmniWatch 2.0",
        "layers": {
            "storage": "operational",
            "topology": "operational",
            "ai": "operational",
            "remediation": "standby",
            "security": "operational",
        },
        "uptime_since": datetime.utcnow().isoformat(),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming."""
    # Authenticate via JWT token in query params
    token = websocket.query_params.get("token", "")
    user = verify_ws_token(token)
    if user is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    await ws_manager.connect(websocket, user=user)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or process incoming messages
            await ws_manager.broadcast(json.dumps({
                "type": "message",
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
