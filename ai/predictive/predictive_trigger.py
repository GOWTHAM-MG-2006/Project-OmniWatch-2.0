"""
OmniWatch 2.0 — NeuroEngine
Component: PredictiveTrigger
Layer: 6
Phase: 2
Purpose: Evaluates forecasts to detect imminent issues and trigger predictive remediation
Inputs: Forecast dict, current metric value, baseline statistics
Outputs: Trigger event for AutoHeal (or None if no issue predicted)
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

METRIC_TO_ISSUE = {
    "cpu_usage": "cpu_exhaustion",
    "cpu_percent": "cpu_exhaustion",
    "memory_usage": "memory_exhaustion",
    "memory_percent": "memory_exhaustion",
    "disk_usage": "disk_exhaustion",
    "disk_percent": "disk_exhaustion",
    "disk_io": "disk_bottleneck",
    "network_rx": "network_saturation",
    "network_tx": "network_saturation",
    "network_bytes": "network_saturation",
    "request_latency": "latency_degradation",
    "response_time": "latency_degradation",
    "p99_latency": "latency_degradation",
    "error_rate": "error_cascade",
    "error_count": "error_cascade",
    "http_5xx": "error_cascade",
    "http_4xx": "error_cascade",
    "container_restarts": "instability",
    "pod_restarts": "instability",
}

THRESHOLDS = {
    "cpu_exhaustion": {"upper_pct": 90.0, "severity_high": 95.0, "severity_critical": 99.0},
    "memory_exhaustion": {"upper_pct": 85.0, "severity_high": 92.0, "severity_critical": 97.0},
    "disk_exhaustion": {"upper_pct": 85.0, "severity_high": 92.0, "severity_critical": 98.0},
    "disk_bottleneck": {"upper_pct": 80.0, "severity_high": 90.0, "severity_critical": 95.0},
    "network_saturation": {"upper_pct": 80.0, "severity_high": 90.0, "severity_critical": 95.0},
    "latency_degradation": {"upper_pct": 200.0, "severity_high": 500.0, "severity_critical": 1000.0},
    "error_cascade": {"upper_pct": 5.0, "severity_high": 10.0, "severity_critical": 25.0},
    "instability": {"upper_pct": 3.0, "severity_high": 5.0, "severity_critical": 10.0},
}

RECOMMENDED_ACTIONS = {
    "cpu_exhaustion": "scale_up",
    "memory_exhaustion": "scale_up",
    "disk_exhaustion": "cleanup_or_expand",
    "disk_bottleneck": "optimize_io",
    "network_saturation": "scale_up",
    "latency_degradation": "scale_up",
    "error_cascade": "rollback",
    "instability": "restart_container",
}


class PredictiveTrigger:
    """Evaluates forecasts and fires trigger events when issues are imminent."""

    def evaluate_forecasts(
        self,
        forecast: dict,
        current_value: float,
        baseline: dict,
    ) -> Optional[dict]:
        horizons = forecast.get("horizons", {})
        if not horizons:
            return None

        metric_name = forecast.get("metric_name", "unknown")
        issue_type = self._classify_issue_type(metric_name)
        if issue_type is None:
            return None

        thresholds = THRESHOLDS.get(issue_type)
        if thresholds is None:
            return None

        # Check each horizon — if any predicts crossing a threshold, trigger
        for horizon_key, horizon_data in horizons.items():
            upper_bound = horizon_data.get("upper_bound", 0.0)
            predicted = horizon_data.get("predicted_value", 0.0)
            pred_ts = horizon_data.get("timestamp", "")

            if self._exceeds_threshold(upper_bound, predicted, issue_type, baseline):
                severity = self._classify_severity(upper_bound, issue_type)
                confidence = self._compute_confidence(predicted, upper_bound, issue_type, baseline)
                action = self._recommend_action(issue_type)

                return self._build_trigger_event(
                    entity_id=forecast.get("entity_id", "unknown"),
                    metric_name=metric_name,
                    issue_type=issue_type,
                    predicted_value=predicted,
                    upper_bound=upper_bound,
                    prediction_timestamp=pred_ts,
                    severity=severity,
                    confidence=confidence,
                    recommended_action=action,
                )

        return None

    def _classify_issue_type(self, metric_name: str) -> Optional[str]:
        metric_lower = metric_name.lower()
        # Direct match
        if metric_lower in METRIC_TO_ISSUE:
            return METRIC_TO_ISSUE[metric_lower]
        # Substring match
        for key, issue in METRIC_TO_ISSUE.items():
            if key in metric_lower or metric_lower in key:
                return issue
        return None

    def _exceeds_threshold(
        self,
        upper_bound: float,
        predicted: float,
        issue_type: str,
        baseline: dict,
    ) -> bool:
        thresholds = THRESHOLDS.get(issue_type, {})
        upper_pct = thresholds.get("upper_pct", 100.0)

        # For percentage-based metrics (CPU, memory, disk)
        if issue_type in (
            "cpu_exhaustion", "memory_exhaustion", "disk_exhaustion",
            "disk_bottleneck", "network_saturation",
        ):
            if upper_bound >= upper_pct:
                return True
            if predicted >= upper_pct:
                return True
            # Also check relative to baseline
            baseline_mean = baseline.get("mean", 0)
            if baseline_mean > 0:
                increase_pct = (upper_bound / baseline_mean) * 100
                if increase_pct >= 150:  # 50% above baseline
                    return True

        # For absolute-value metrics (latency, errors)
        if issue_type in ("latency_degradation", "error_cascade", "instability"):
            if upper_bound >= upper_pct:
                return True
            if predicted >= upper_pct:
                return True

        return False

    def _classify_severity(self, upper_bound: float, issue_type: str) -> str:
        thresholds = THRESHOLDS.get(issue_type, {})
        if upper_bound >= thresholds.get("severity_critical", float("inf")):
            return "CRITICAL"
        if upper_bound >= thresholds.get("severity_high", float("inf")):
            return "HIGH"
        return "MEDIUM"

    def _compute_confidence(
        self,
        predicted: float,
        upper_bound: float,
        issue_type: str,
        baseline: dict,
    ) -> float:
        baseline_mean = baseline.get("mean", 0)
        baseline_std = baseline.get("std", 1)

        # Confidence based on how far above threshold
        thresholds = THRESHOLDS.get(issue_type, {})
        threshold_val = thresholds.get("upper_pct", 100.0)

        # z-score of upper_bound relative to baseline
        if baseline_std > 0 and baseline_mean > 0:
            z_score = (upper_bound - baseline_mean) / baseline_std
        else:
            z_score = 0

        # Map z-score to confidence [0.5, 0.99]
        raw_confidence = 0.5 + min(max(z_score / 5.0, 0), 0.49)
        return round(raw_confidence, 2)

    def _recommend_action(self, issue_type: str) -> str:
        return RECOMMENDED_ACTIONS.get(issue_type, "investigate")

    def _build_trigger_event(
        self,
        entity_id: str,
        metric_name: str,
        issue_type: str,
        predicted_value: float,
        upper_bound: float,
        prediction_timestamp: str,
        severity: str,
        confidence: float,
        recommended_action: str,
    ) -> dict:
        return {
            "trigger_type": "predictive",
            "entity_id": entity_id,
            "metric_name": metric_name,
            "issue_type": issue_type,
            "predicted_value": round(predicted_value, 2),
            "upper_bound": round(upper_bound, 2),
            "prediction_timestamp": prediction_timestamp,
            "severity": severity,
            "confidence": confidence,
            "recommended_action": recommended_action,
            "triggered_at": datetime.utcnow().isoformat(),
        }
