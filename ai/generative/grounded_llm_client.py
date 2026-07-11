"""OmniWatch 2.0 — NeuroEngine
Component: Grounded LLM Client
Layer: 6
Phase: 2
Purpose: BYOM async LLM client with evidence-grounding system prompt and mock fallback
Inputs: Prompt string + optional context (RootCauseObject)
Outputs: Dict with response text, model name, and token usage"""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """You are OmniWatch 2.0's incident analysis assistant.
You MUST ground every claim in the evidence provided.
Rules:
1. Only reference entities, metrics, and values present in the input data.
2. Never fabricate entity names, metric values, or timestamps.
3. When citing evidence, reference the evidence_id from the chain.
4. If the evidence is insufficient, say so explicitly.
5. Use the exact severity, confidence, and deviation values from the RootCauseObject.
6. Do NOT speculate beyond what the data supports."""

EVIDENCE_GROUNDING_SUFFIX = """
Grounding instructions:
- Every factual claim must trace to an evidence_id or field in the RootCauseObject.
- Do not invent blast radius, affected user counts, or revenue figures not in the data.
- If you are uncertain, use hedging language like "may indicate" rather than definitive statements."""


class GroundedLLMClient:
    """Async BYOM LLM client with evidence-grounding system prompt.

    Supports Ollama/vLLM-compatible APIs. Falls back to a deterministic
    mock response when no inference server is available.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
        timeout: float = 30.0,
    ):
        self._base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self._model = model or os.environ.get("OLLAMA_MODEL", "qwen3:8b")
        self._system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self._timeout = timeout

    async def generate(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        include_grounding_suffix: bool = True,
    ) -> dict[str, Any]:
        """Generate a response from the LLM with evidence grounding.

        Args:
            prompt: The user prompt to send to the LLM.
            context: Optional RootCauseObject to inject into the prompt.
            include_grounding_suffix: Whether to append grounding instructions.

        Returns:
            Dict with keys: response (str), model (str), usage (dict), timestamp (str).
        """
        full_prompt = self._build_prompt(prompt, context, include_grounding_suffix)

        try:
            result = await self._call_llm(full_prompt)
            logger.info("LLM response received: %d chars", len(result["response"]))
            return result
        except Exception as e:
            logger.warning("LLM call failed (%s), using mock response", e)
            return self._mock_response(full_prompt, context)

    def _build_prompt(
        self,
        prompt: str,
        context: dict[str, Any] | None,
        include_grounding_suffix: bool,
    ) -> str:
        """Assemble the full prompt with optional RootCauseObject context."""
        parts = [prompt]

        if context:
            parts.append("\n\nRootCauseObject data:\n")
            parts.append(json.dumps(context, indent=2, default=str))

        if include_grounding_suffix:
            parts.append(EVIDENCE_GROUNDING_SUFFIX)

        return "".join(parts)

    async def _call_llm(self, prompt: str) -> dict[str, Any]:
        """Call the Ollama API endpoint.

        Uses httpx for async HTTP. The endpoint follows Ollama's native
        /api/chat format for chat completions.

        Raises:
            ConnectionError: If the inference server is unreachable.
            httpx.HTTPError: On HTTP-level failures.
        """
        try:
            import httpx
        except ImportError:
            raise ConnectionError("httpx is not installed; cannot call LLM API")

        url = f"{self._base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 2048,
            },
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data.get("message", {}).get("content", "")
        return {
            "response": content,
            "model": data.get("model", self._model),
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _mock_response(
        self, prompt: str, context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Generate a deterministic mock response for testing.

        Produces a plausible incident analysis grounded in the provided context,
        without requiring an actual LLM inference server.
        """
        if context and "root_cause" in context:
            rc = context["root_cause"]
            entity = rc.get("entity", "unknown entity")
            entity_type = rc.get("entity_type", "unknown type")
            deviation = rc.get("deviation", "N/A")
            causal_score = rc.get("causal_score", 0)

            severity = context.get("severity", "UNKNOWN")
            confidence = context.get("confidence", 0)
            problem_id = context.get("problem_id", "PRB-UNKNOWN")

            blast = context.get("blast_radius", [])
            blast_summary = ", ".join(
                f"{b['entity']} ({b.get('impact', 'degraded')})" for b in blast[:3]
            ) if blast else "no downstream impact identified"

            biz = context.get("business_impact", {})
            affected = biz.get("affected_users", 0)
            revenue = biz.get("estimated_revenue_at_risk_usd_per_hour", 0)

            evidence_chain = context.get("evidence_chain", [])
            evidence_refs = ", ".join(
                e.get("evidence_id", "N/A") for e in evidence_chain[:3]
            ) if evidence_chain else "N/A"

            response_text = (
                f"## Incident Analysis: {problem_id}\n\n"
                f"**Severity:** {severity} | **Confidence:** {confidence:.0%}\n\n"
                f"### Root Cause\n"
                f"The root cause has been identified as **{entity}** ({entity_type}). "
                f"The metric deviation observed is {deviation}, with a causal confidence "
                f"score of {causal_score:.2f}.\n\n"
                f"### Evidence Chain\n"
                f"Analysis traced through evidence references {evidence_refs}.\n\n"
                f"### Blast Radius\n"
                f"Downstream impact: {blast_summary}.\n\n"
                f"### Business Impact\n"
                f"Affected users: ~{affected:,}. "
                f"Estimated revenue at risk: ${revenue:,.0f}/hour.\n\n"
                f"### Recommendation\n"
                f"Immediate investigation of {entity} is recommended. "
                f"Review recent configuration changes and resource utilization."
            )
        else:
            response_text = (
                "## Incident Analysis\n\n"
                "No RootCauseObject data was provided. "
                "Please supply a RootCauseObject for a grounded analysis."
            )

        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:8]
        return {
            "response": response_text,
            "model": f"mock-{prompt_hash}",
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(response_text.split()),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
