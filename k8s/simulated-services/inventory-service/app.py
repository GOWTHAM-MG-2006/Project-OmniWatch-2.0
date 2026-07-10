"""
OmniWatch 2.0 — Simulated Services
Component: Inventory Service (Fake)
Layer: Testing
Phase: 1
Purpose: Simulated inventory microservice for testing telemetry ingestion
Inputs: HTTP requests
Outputs: Mock inventory responses, emits telemetry events
"""

import os
import time
import random
import logging
from datetime import datetime
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simulated Inventory Service")

# Simulated inventory
INVENTORY = {f"ITEM-{i:04d}": random.randint(0, 100) for i in range(100)}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "inventory-service", "version": "1.0.0"}


@app.get("/check-stock/{item_id}")
async def check_stock(item_id: str):
    time.sleep(random.uniform(0.005, 0.1))
    stock = INVENTORY.get(item_id, 0)
    return {
        "item_id": item_id,
        "in_stock": stock > 0,
        "quantity": stock,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/reserve")
async def reserve_item(data: dict | None = None):
    time.sleep(random.uniform(0.01, 0.15))
    item_id = data.get("item_id", "ITEM-0001") if data else "ITEM-0001"
    if INVENTORY.get(item_id, 0) > 0:
        INVENTORY[item_id] -= 1
        return {"status": "reserved", "item_id": item_id, "remaining": INVENTORY[item_id]}
    return {"status": "out_of_stock", "item_id": item_id}


@app.get("/metrics")
async def metrics_endpoint():
    return {
        "total_items": len(INVENTORY),
        "low_stock_count": sum(1 for v in INVENTORY.values() if v < 10),
        "latency_p50_ms": round(random.uniform(5, 30), 2),
        "latency_p95_ms": round(random.uniform(50, 150), 2),
    }
