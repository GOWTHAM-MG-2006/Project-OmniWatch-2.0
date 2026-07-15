"""
OmniWatch 2.0 — GhostCollector
Component: LLM Observer
Layer: 2
Phase: 3
Purpose: LLM/GenAI workload observability — tracks model, tokens, latency, cost per call
Inputs: LLM API calls (OpenAI, Anthropic, Ollama endpoints)
Outputs: LLM metrics → Kafka omniwatch.telemetry.raw
Technology: Python (httpx for async interception, framework hooks)
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from config import config

logger = logging.getLogger(__name__)

# Approximate cost per 1K tokens (USD) by model family
COST_PER_1K_TOKENS = {
    "gpt-4": 0.03,
    "gpt-4o": 0.005,
    "gpt-4o-mini": 0.00015,
    "gpt-3.5-turbo": 0.0005,
    "claude-3-opus": 0.015,
    "claude-3-sonnet": 0.003,
    "claude-3-haiku": 0.00025,
    "llama3": 0.0,
    "qwen": 0.0,
    "gemini-pro": 0.00125,
    "default": 0.001,
}


class LLMObserver:
    """Tracks LLM/GenAI API calls for observability.

    Intercepts LLM calls to record model name, token usage (in/out),
    latency, and estimated cost per call.
    """

    def __init__(self):
        self._call_count = 0

    def wrap_call(self, model: str, endpoint: str) -> dict[str, Any]:
        """Wrap an LLM call to record observability metrics.

        Args:
            model: Model name (e.g., "gpt-4o", "llama3").
            endpoint: LLM API endpoint URL.

        Returns:
            LLM metrics dict matching OmniWatch telemetry schema.
        """
        self._call_count += 1
        return {
            "entity_id": f"llm-{model}",
            "entity_type": "GenAIService",
            "entity_layer": 7,
            "metric_name": "llm_call",
            "model": model,
            "endpoint": endpoint,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def record_response(
        self,
        metrics: dict[str, Any],
        response_data: dict[str, Any],
        latency_ms: float,
    ) -> dict[str, Any]:
        """Record metrics from an LLM API response.

        Args:
            metrics: Base metrics dict from wrap_call.
            response_data: Response JSON from LLM API.
            latency_ms: Call latency in milliseconds.

        Returns:
            Complete LLM telemetry record.
        """
        model = metrics.get("model", "unknown")
        usage = response_data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens

        cost_per_1k = COST_PER_1K_TOKENS.get(model, COST_PER_1K_TOKENS["default"])
        estimated_cost = (total_tokens / 1000) * cost_per_1k

        return {
            "entity_id": metrics.get("entity_id", f"llm-{model}"),
            "entity_type": "GenAIService",
            "entity_layer": 7,
            "metric_name": "llm_call",
            "model": model,
            "endpoint": metrics.get("endpoint", ""),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "latency_ms": round(latency_ms, 2),
            "estimated_cost_usd": round(estimated_cost, 6),
            "success": response_data.get("choices") is not None,
            "timestamp": metrics.get("timestamp", datetime.now(timezone.utc).isoformat()),
        }

    async def intercept_openai(
        self,
        base_url: str,
        api_key: str,
        model: str,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> dict[str, Any]:
        """Intercept an OpenAI-compatible API call.

        Args:
            base_url: API base URL (e.g., "https://api.openai.com/v1").
            api_key: API key.
            model: Model name.
            messages: Chat messages.

        Returns:
            LLM telemetry record.
        """
        metrics = self.wrap_call(model, base_url)
        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=config.LLM_HTTP_TIMEOUT) as client:
                resp = await client.post(
                    f"{base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": model, "messages": messages, **kwargs},
                )
                latency_ms = (time.time() - start) * 1000
                response_data = resp.json()
                return self.record_response(metrics, response_data, latency_ms)
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            logger.warning("LLM interception failed: %s", e)
            return self.record_response(metrics, {"usage": {}}, latency_ms)

    def format_for_kafka(self, record: dict[str, Any]) -> str:
        """Format an LLM telemetry record for Kafka publishing."""
        return json.dumps(record, default=str)
