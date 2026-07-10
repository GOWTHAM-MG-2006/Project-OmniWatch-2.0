"""
OmniWatch 2.0 — StreamForge
Component: PII Engine
Layer: 3
Phase: 1
Purpose: Privacy-by-default PII detection and anonymization (Presidio stub)
Inputs: Telemetry data containing potential PII
Outputs: Anonymized telemetry with PII redacted
"""

import os
import re
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# PII anonymization actions
PII_ACTIONS = {
    "mask": "Replace PII with asterisks",
    "hash": "Replace PII with SHA256 hashes",
    "drop": "Remove PII entirely",
    "tokenize": "Replace PII with tokens",
}

# Try importing Presidio for ML-based detection
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    _presidio_available = True
except ImportError:
    _presidio_available = False

# Common PII patterns
PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "aws_key": r"\b(AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}\b",
    "api_key": r"\b[a-fA-F0-9]{32}\b",
}

# Entity types that commonly contain PII in logs
PII_RISKY_FIELDS = {
    "message", "log_message", "error_message", "stack_trace",
    "user_agent", "url", "query", "headers", "body",
}


class PIIEngine:
    """PII detection and anonymization engine."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._compiled_patterns = {
            name: re.compile(pattern)
            for name, pattern in PII_PATTERNS.items()
        }

    def detect_pii(self, text: str) -> list[dict[str, Any]]:
        """Detect PII entities in text. Returns list of detected PII with type and position."""
        if not self.enabled or not text:
            return []

        detections = []
        for pii_type, pattern in self._compiled_patterns.items():
            for match in pattern.finditer(text):
                detections.append({
                    "type": pii_type,
                    "start": match.start(),
                    "end": match.end(),
                    "value": match.group(),
                })

        return detections

    def anonymize(self, text: str, detections: list[dict[str, Any]] | None = None) -> str:
        """Anonymize detected PII in text."""
        if not self.enabled or not text:
            return text

        if detections is None:
            detections = self.detect_pii(text)

        if not detections:
            return text

        # Replace from end to start to preserve positions
        anonymized = text
        for detection in sorted(detections, key=lambda d: d["start"], reverse=True):
            pii_type = detection["type"]
            start = detection["start"]
            end = detection["end"]

            if pii_type == "email":
                replacement = "[EMAIL_REDACTED]"
            elif pii_type == "phone":
                replacement = "[PHONE_REDACTED]"
            elif pii_type == "ip_address":
                replacement = "[IP_REDACTED]"
            elif pii_type == "ssn":
                replacement = "[SSN_REDACTED]"
            elif pii_type == "credit_card":
                replacement = "[CC_REDACTED]"
            elif pii_type == "aws_key":
                replacement = "[AWS_KEY_REDACTED]"
            elif pii_type == "api_key":
                replacement = "[API_KEY_REDACTED]"
            else:
                replacement = "[PII_REDACTED]"

            anonymized = anonymized[:start] + replacement + anonymized[end:]

        return anonymized

    def anonymize_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Anonymize PII in an entire event."""
        if not self.enabled:
            return event

        anonymized = dict(event)

        # Check fields that commonly contain PII
        for field in PII_RISKY_FIELDS:
            if field in anonymized and isinstance(anonymized[field], str):
                detections = self.detect_pii(anonymized[field])
                if detections:
                    anonymized[field] = self.anonymize(anonymized[field], detections)
                    logger.debug("Anonymized %d PII instances in field '%s'", len(detections), field)

        return anonymized

    def anonymize_batch(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Anonymize a batch of events."""
        return [self.anonymize_event(event) for event in events]

    def detect_pii_with_presidio(self, text: str) -> list[dict[str, Any]]:
        """Detect PII using Microsoft Presidio (ML-based). Falls back to regex if unavailable."""
        if not _presidio_available:
            logger.debug("Presidio not installed, falling back to regex detection")
            return self.detect_pii(text)

        try:
            analyzer = AnalyzerEngine()
            results = analyzer.analyze(text=text, language="en")
            return [
                {
                    "type": r.entity_type,
                    "start": r.start,
                    "end": r.end,
                    "value": text[r.start:r.end],
                    "score": r.score,
                }
                for r in results
            ]
        except Exception as e:
            logger.warning("Presidio analysis failed, falling back to regex: %s", e)
            return self.detect_pii(text)

    def _mask_pii(self, text: str, pii_items: list) -> str:
        """Replace PII with asterisks."""
        anonymized = text
        for item in sorted(pii_items, key=lambda d: d["start"], reverse=True):
            length = item["end"] - item["start"]
            replacement = "*" * length
            anonymized = anonymized[:item["start"]] + replacement + anonymized[item["end"]:]
        return anonymized

    def _hash_pii(self, text: str, pii_items: list) -> str:
        """Replace PII with SHA256 hashes (first 12 chars)."""
        import hashlib
        anonymized = text
        for item in sorted(pii_items, key=lambda d: d["start"], reverse=True):
            original = item["value"]
            hashed = hashlib.sha256(original.encode()).hexdigest()[:12]
            anonymized = anonymized[:item["start"]] + hashed + anonymized[item["end"]:]
        return anonymized

    def _tokenize_pii(self, text: str, pii_items: list) -> str:
        """Replace PII with labeled tokens like <EMAIL_0>, <PHONE_1>."""
        counter: dict[str, int] = {}
        anonymized = text
        for item in sorted(pii_items, key=lambda d: d["start"], reverse=True):
            pii_type = item["type"]
            idx = counter.get(pii_type, 0)
            counter[pii_type] = idx + 1
            token = f"<{pii_type.upper()}_{idx}>"
            anonymized = anonymized[:item["start"]] + token + anonymized[item["end"]:]
        return anonymized

    def anonymize_with_action(self, text: str, action: str) -> str:
        """Anonymize PII using the specified action.

        Supported actions: mask, hash, drop, tokenize.
        """
        if not self.enabled or not text:
            return text

        detections = self.detect_pii(text)
        if not detections:
            return text

        if action == "mask":
            return self._mask_pii(text, detections)
        elif action == "hash":
            return self._hash_pii(text, detections)
        elif action == "drop":
            anonymized = text
            for item in sorted(detections, key=lambda d: d["start"], reverse=True):
                anonymized = anonymized[:item["start"]] + anonymized[item["end"]:]
            return anonymized
        elif action == "tokenize":
            return self._tokenize_pii(text, detections)
        else:
            logger.warning("Unknown PII action '%s', falling back to default anonymize", action)
            return self.anonymize(text, detections)
