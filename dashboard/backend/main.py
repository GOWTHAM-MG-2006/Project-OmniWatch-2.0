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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from dashboard.backend.routes import (
    incidents, topology, metrics, approvals,
    knowledge, simulations, security, config_drift, reports,
)
from dashboard.backend.websocket import ConnectionManager

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
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    await ws_manager.connect(websocket)
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
