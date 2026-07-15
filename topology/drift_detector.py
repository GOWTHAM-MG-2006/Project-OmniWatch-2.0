"""
OmniWatch 2.0 — TopoBrain
Component: Drift Detector
Layer: 5
Phase: 1
Purpose: Compares runtime vs declared architecture to detect configuration drift
Inputs: Runtime graph state, declared configuration (YAML/JSON)
Outputs: Drift events with severity and recommended remediation
"""

import os
import json
import logging
from typing import Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DriftDetector:
    """Detects drift between runtime and declared architecture."""

    def __init__(self):
        self._baseline: dict[str, Any] = {}
        self._drift_history: list[dict[str, Any]] = []

    def set_baseline(self, declared_config: dict[str, Any]):
        """Set the declared (desired) architecture baseline."""
        self._baseline = declared_config
        logger.info("Baseline set with %d entities", len(declared_config.get("entities", {})))

    def compare(
        self,
        runtime_graph: dict[str, Any],
        declared_config: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Compare runtime state against declared configuration.

        Returns a list of drift events.
        """
        config = declared_config or self._baseline
        if not config:
            logger.warning("No baseline configured for drift detection")
            return []

        drifts = []

        declared_entities = config.get("entities", {})
        runtime_entities = runtime_graph.get("entities", {})

        # Check for entities in runtime but not in declared (unauthorized additions)
        for entity_id, runtime_data in runtime_entities.items():
            if entity_id not in declared_entities:
                drifts.append(self._create_drift(
                    drift_id=f"DRF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{entity_id}",
                    drifted_entity=entity_id,
                    drift_type="UNAUTHORIZED_ADDITION",
                    expected_state={},
                    actual_state=runtime_data,
                    severity="HIGH",
                ))
            else:
                # Check for property drift
                declared_data = declared_entities[entity_id]
                property_drifts = self._compare_properties(entity_id, declared_data, runtime_data)
                drifts.extend(property_drifts)

        # Check for entities in declared but not in runtime (missing entities)
        for entity_id in declared_entities:
            if entity_id not in runtime_entities:
                drifts.append(self._create_drift(
                    drift_id=f"DRF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{entity_id}",
                    drifted_entity=entity_id,
                    drift_type="MISSING_ENTITY",
                    expected_state=declared_entities[entity_id],
                    actual_state={},
                    severity="MEDIUM",
                ))

        self._drift_history.extend(drifts)
        logger.info("Drift detection complete: %d drifts found", len(drifts))
        return drifts

    def detect_drift(self, entity_id: str, actual: dict[str, Any]) -> dict[str, Any] | None:
        """Detect drift for a single entity."""
        declared = self._baseline.get("entities", {}).get(entity_id)
        if not declared:
            return None

        drifts = self._compare_properties(entity_id, declared, actual)
        return drifts[0] if drifts else None

    def _compare_properties(
        self,
        entity_id: str,
        declared: dict[str, Any],
        actual: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Compare properties of a single entity."""
        drifts = []
        for key, expected_value in declared.items():
            actual_value = actual.get(key)
            if actual_value != expected_value:
                drifts.append(self._create_drift(
                    drift_id=f"DRF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{entity_id}-{key}",
                    drifted_entity=entity_id,
                    drift_type="PROPERTY_MISMATCH",
                    expected_state={key: expected_value},
                    actual_state={key: actual_value},
                    severity="LOW" if key != "image" else "HIGH",
                ))
        return drifts

    def _create_drift(
        self,
        drift_id: str,
        drifted_entity: str,
        drift_type: str,
        expected_state: dict[str, Any],
        actual_state: dict[str, Any],
        severity: str,
    ) -> dict[str, Any]:
        """Create a drift event record with dynamic confidence."""
        now = datetime.utcnow()
        last_known = datetime.utcnow()
        time_diff = max(0, (now - last_known).total_seconds())
        time_factor = min(1.0, max(0.1, time_diff / 3600))
        magnitude = len(str(expected_state)) + len(str(actual_state))
        magnitude_factor = min(1.0, magnitude / 200)
        entity_factor = 0.5
        confidence = round(time_factor * 0.4 + magnitude_factor * 0.4 + entity_factor * 0.2, 2)
        confidence = max(0.5, min(0.99, confidence))
        return {
            "drift_id": drift_id,
            "drifted_entity": drifted_entity,
            "drift_type": drift_type,
            "expected_state": expected_state,
            "actual_state": actual_state,
            "severity": severity,
            "confidence": confidence,
            "timestamp": now.isoformat(),
            "status": "detected",
        }

    def get_drift_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent drift history."""
        return self._drift_history[-limit:]

    def report_drift(self, drift: dict[str, Any]) -> str:
        """Generate a human-readable drift report."""
        return (
            f"Drift Detected: {drift['drift_type']}\n"
            f"Entity: {drift['drifted_entity']}\n"
            f"Severity: {drift['severity']}\n"
            f"Expected: {json.dumps(drift['expected_state'], indent=2)}\n"
            f"Actual: {json.dumps(drift['actual_state'], indent=2)}\n"
            f"Time: {drift['timestamp']}"
        )
