"""
OmniWatch 2.0 — Simulated Services
Component: Payment Service (Fake)
Layer: Testing
Phase: 1
Purpose: Simulated payment microservice for testing telemetry ingestion
Inputs: HTTP requests
Outputs: Mock payment responses, emits telemetry events
"""

import os
import time
import random
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simulated Payment Service")

# Simulated state
PAYMENT_COUNT = 0


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "payment-service", "version": "1.0.0"}


@app.post("/pay")
async def process_payment(data: dict | None = None):
    global PAYMENT_COUNT
    PAYMENT_COUNT += 1

    # Simulate processing time
    processing_time = random.uniform(0.01, 0.5)
    time.sleep(processing_time)

    # Simulate occasional failures
    if random.random() < 0.05:
        logger.error("Payment processing failed for order %s", data)
        return JSONResponse(
            status_code=500,
            content={"error": "Payment processing failed", "order_id": data},
        )

    logger.info("Payment processed: %s (%.3fs)", PAYMENT_COUNT, processing_time)
    return {
        "status": "success",
        "payment_id": f"PAY-{PAYMENT_COUNT:06d}",
        "processing_time_ms": round(processing_time * 1000, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/refund")
async def refund_payment(data: dict | None = None):
    # Simulate refund processing
    time.sleep(random.uniform(0.01, 0.2))
    return {"status": "refund_initiated", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
async def metrics_endpoint():
    """Expose simulated Prometheus metrics."""
    return {
        "payment_count": PAYMENT_COUNT,
        "error_rate": round(random.uniform(0, 0.05), 4),
        "latency_p50_ms": round(random.uniform(10, 50), 2),
        "latency_p95_ms": round(random.uniform(100, 300), 2),
        "latency_p99_ms": round(random.uniform(300, 800), 2),
    }
