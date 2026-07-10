"""
OmniWatch 2.0 — StreamForge
Component: Receipt Validation
Layer: 3
Phase: 1
Purpose: Multi-protocol ingest validation for metrics, logs, and traces
Inputs: Raw telemetry events from GhostCollector
Outputs: Validated events or rejection with reason
"""

import os
import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Required fields per event type
REQUIRED_FIELDS = {
    "metric": ["entity_id", "metric_name", "metric_value", "timestamp"],
    "log": ["entity_id", "message", "timestamp"],
    "trace": ["trace_id", "span_id", "service_name", "start_time"],
}

# Allowed entity types
VALID_ENTITY_TYPES = {
    "service", "process", "host", "infrastructure", "database",
    "genai_service", "business_transaction", "cost_center",
}

# Allowed log levels
VALID_LOG_LEVELS = {"debug", "info", "warn", "warning", "error", "fatal", "critical"}

# Allowed trace status codes
VALID_TRACE_STATUSES = {"ok", "error", "unset"}


class ReceiptValidation:
    """Multi-protocol ingest validation for telemetry data."""

    def validate_metric(self, event: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate a metric event. Returns (is_valid, error_reason)."""
        # Check required fields
        missing = [f for f in REQUIRED_FIELDS["metric"] if f not in event]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"

        # Validate metric_value is numeric
        if not isinstance(event["metric_value"], (int, float)):
            return False, f"metric_value must be numeric, got {type(event['metric_value']).__name__}"

        # Validate entity_type if present
        if "entity_type" in event:
            if event["entity_type"] not in VALID_ENTITY_TYPES:
                return False, f"Invalid entity_type: {event['entity_type']}"

        # Validate timestamp
        ts = event.get("timestamp")
        if isinstance(ts, str):
            try:
                datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                return False, f"Invalid timestamp format: {ts}"

        return True, None

    def validate_log(self, event: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate a log event. Returns (is_valid, error_reason)."""
        missing = [f for f in REQUIRED_FIELDS["log"] if f not in event]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"

        # Validate log_level if present
        if "log_level" in event:
            if event["log_level"].lower() not in VALID_LOG_LEVELS:
                return False, f"Invalid log_level: {event['log_level']}"

        # Validate message is non-empty
        if not event["message"]:
            return False, "Log message cannot be empty"

        return True, None

    def validate_trace(self, event: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate a trace/span event. Returns (is_valid, error_reason)."""
        missing = [f for f in REQUIRED_FIELDS["trace"] if f not in event]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"

        # Validate status_code if present
        if "status_code" in event:
            if event["status_code"].lower() not in VALID_TRACE_STATUSES:
                return False, f"Invalid trace status_code: {event['status_code']}"

        # Validate duration_ms if present
        if "duration_ms" in event:
            if not isinstance(event["duration_ms"], (int, float)):
                return False, "duration_ms must be numeric"
            if event["duration_ms"] < 0:
                return False, "duration_ms cannot be negative"

        return True, None

    def validate(self, event: dict[str, Any]) -> tuple[bool, str | None]:
        """Auto-detect event type and validate."""
        if "metric_name" in event or "metric_value" in event:
            return self.validate_metric(event)
        elif "log_level" in event or "message" in event:
            return self.validate_log(event)
        elif "trace_id" in event or "span_id" in event:
            return self.validate_trace(event)
        else:
            return False, "Unable to determine event type"

    def validate_batch(self, events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Validate a batch of events. Returns (valid_events, invalid_events)."""
        valid = []
        invalid = []
        for event in events:
            is_valid, reason = self.validate(event)
            if is_valid:
                valid.append(event)
            else:
                invalid.append({**event, "_validation_error": reason})
                logger.warning("Invalid event: %s", reason)
        return valid, invalid
