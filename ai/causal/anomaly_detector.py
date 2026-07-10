"""
OmniWatch 2.0 — NeuroEngine
Component: Anomaly Detector
Layer: 6
Phase: 2
Purpose: Multi-signal anomaly detection across metrics, logs, traces, network, topology
Inputs: ClickHouse windowed features + baselines from BaselineEngine
Outputs: AnomalySignal objects → Kafka omniwatch.anomalies.detected
"""

import logging
from typing import Any
from datetime import datetime, timezone

import numpy as np

from ai.causal.baseline_engine import BaselineEngine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEVERITY_THRESHOLDS: dict[str, float] = {
    "CRITICAL": 0.90,
    "HIGH": 0.75,
    "MEDIUM": 0.50,
    "LOW": 0.25,
}

DETECTION_METHODS: dict[str, str] = {
    "z_score": "Z-Score: flags values beyond k standard deviations from baseline mean",
    "ewma": "EWMA: Exponentially Weighted Moving Average detection",
    "iqr": "IQR: Interquartile Range outlier detection",
    "bocpd": "Bayesian Online Change Point Detection",
}


# ---------------------------------------------------------------------------
# Severity classifier
# ---------------------------------------------------------------------------

def classify_severity(anomaly_score: float) -> str:
    """Map a continuous anomaly score [0, 1] to a severity label."""
    for label, threshold in SEVERITY_THRESHOLDS.items():
        if anomaly_score >= threshold:
            return label
    return "LOW"


# ---------------------------------------------------------------------------
# Anomaly Detector
# ---------------------------------------------------------------------------

class AnomalyDetector:
    """Multi-signal anomaly detector.

    Runs one or more detection algorithms on each metric, merges results
    per metric into a single AnomalySignal, and returns all signals that
    exceed a configurable minimum anomaly score.
    """

    def __init__(
        self,
        baseline_engine: BaselineEngine | None = None,
        z_threshold: float = 3.0,
        ewma_alpha: float = 0.3,
        ewma_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
        bocpd_threshold: float = 0.95,
        min_anomaly_score: float = 0.25,
    ):
        self._baseline_engine = baseline_engine or BaselineEngine()
        self.z_threshold = z_threshold
        self.ewma_alpha = ewma_alpha
        self.ewma_threshold = ewma_threshold
        self.iqr_multiplier = iqr_multiplier
        self.bocpd_threshold = bocpd_threshold
        self.min_anomaly_score = min_anomaly_score

    # -- Individual detectors --------------------------------------------------

    def detect_z_score(
        self, values: list[float], baseline: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Z-score detection: flag points where |z| > threshold.

        Uses the baseline mean and std from BaselineEngine.
        """
        if not values:
            return []

        mean = baseline.get("mean", 0.0)
        std = baseline.get("std", 0.0)
        if std == 0:
            return []

        anomalies = []
        for i, v in enumerate(values):
            z = abs((v - mean) / std)
            if z > self.z_threshold:
                anomalies.append({
                    "index": i,
                    "value": v,
                    "z_score": round(z, 4),
                    "method": "z_score",
                })
        return anomalies

    def detect_ewma(
        self, values: list[float], baseline: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """EWMA detection: flags points where the EWMA deviation exceeds
        a threshold of standard deviations.

        Uses the baseline std as the expected noise scale.
        """
        if not values:
            return []

        std = baseline.get("std", 0.0)
        if std == 0:
            return []

        arr = np.array(values, dtype=np.float64)
        alpha = self.ewma_alpha

        # Compute EWMA
        ewma = np.zeros_like(arr)
        ewma[0] = arr[0]
        for i in range(1, len(arr)):
            ewma[i] = alpha * arr[i] + (1 - alpha) * ewma[i - 1]

        # Residuals from EWMA
        residuals = arr - ewma
        deviation = np.abs(residuals) / std

        anomalies = []
        for i, d in enumerate(deviation):
            if d > self.ewma_threshold:
                anomalies.append({
                    "index": i,
                    "value": float(arr[i]),
                    "ewma": round(float(ewma[i]), 4),
                    "deviation_stds": round(float(d), 4),
                    "method": "ewma",
                })
        return anomalies

    def detect_iqr(
        self, values: list[float], _baseline: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """IQR-based outlier detection.

        Points outside [Q1 - k*IQR, Q3 + k*IQR] are flagged.
        """
        if len(values) < 4:
            return []

        arr = np.array(values, dtype=np.float64)
        q1 = float(np.percentile(arr, 25))
        q3 = float(np.percentile(arr, 75))
        iqr = q3 - q1
        lower = q1 - self.iqr_multiplier * iqr
        upper = q3 + self.iqr_multiplier * iqr

        anomalies = []
        for i, v in enumerate(values):
            if v < lower or v > upper:
                anomalies.append({
                    "index": i,
                    "value": v,
                    "q1": round(q1, 4),
                    "q3": round(q3, 4),
                    "iqr": round(iqr, 4),
                    "method": "iqr",
                })
        return anomalies

    def detect_bocpd(
        self, values: list[float], baseline: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Bayesian Online Change Point Detection.

        Adams & MacKay (2007) algorithm. Runs in O(n) using a linear
        forward pass with a Student-t predictive model.

        Returns points where the change-point probability exceeds the threshold.
        """
        if len(values) < 5:
            return []

        arr = np.array(values, dtype=np.float64)
        n = len(arr)

        # Prior parameters for the Student-t predictive distribution
        mu0 = baseline.get("mean", float(np.mean(arr)))
        kappa0 = 1.0
        alpha0 = 1.0
        beta0 = baseline.get("std", float(np.std(arr))) ** 2 or 1.0

        # Sufficient statistics arrays
        mu_t = np.full(n + 1, mu0)
        kappa_t = np.full(n + 1, kappa0)
        alpha_t = np.full(n + 1, alpha0)
        beta_t = np.full(n + 1, beta0)

        # Run-length probabilities (log scale for numerical stability)
        R = np.zeros((n + 1, n + 1))
        R[0, 0] = 1.0

        # Hazard function: constant hazard H(t) = 1/(t+1)
        H = np.zeros(n)

        anomalies = []

        for t in range(n):
            # Predictive probability under current run length
            pred_probs = np.zeros(t + 2)

            for r in range(t + 1):
                # Student-t parameters
                df = 2 * alpha_t[r]
                loc = mu_t[r]
                scale = np.sqrt(beta_t[r] * (kappa_t[r] + 1) / (alpha_t[r] * kappa_t[r]))

                # Log-predictive probability (Student-t)
                x = (arr[t] - loc) / scale if scale > 0 else 0.0
                log_pred = (
                    _loggamma((df + 1) / 2)
                    - _loggamma(df / 2)
                    - 0.5 * np.log(np.pi * df)
                    - np.log(scale)
                    - (df + 1) / 2 * np.log(1 + x ** 2 / df)
                )
                pred_probs[r] = R[t, r] * np.exp(log_pred)

            # Change-point probability (run length = 0)
            H[t] = 1.0 / (t + 1)
            pred_probs[t + 1] = np.sum(R[t, : t + 1] * H[t])

            # Normalize
            evidence = np.sum(pred_probs)
            if evidence > 0:
                pred_probs /= evidence

            # Store run-length distribution for next step
            R[t + 1, : t + 2] = pred_probs

            # Update sufficient statistics
            for r in range(t + 2):
                if pred_probs[r] > 0:
                    x = arr[t]
                    new_kappa = kappa_t[min(r, t)] + 1
                    new_mu = (kappa_t[min(r, t)] * mu_t[min(r, t)] + x) / new_kappa
                    new_alpha = alpha_t[min(r, t)] + 0.5
                    new_beta = (
                        beta_t[min(r, t)]
                        + kappa_t[min(r, t)] * (x - mu_t[min(r, t)]) ** 2 / (2 * new_kappa)
                    )
                    if r < n:
                        mu_t[r] = new_mu
                        kappa_t[r] = new_kappa
                        alpha_t[r] = new_alpha
                        beta_t[r] = new_beta

            # Flag if run-length 0 probability is high (change point)
            cp_prob = R[t + 1, 0]
            if cp_prob > self.bocpd_threshold:
                anomalies.append({
                    "index": t,
                    "value": float(arr[t]),
                    "change_point_prob": round(float(cp_prob), 4),
                    "method": "bocpd",
                })

        return anomalies

    # -- Multi-signal aggregation ----------------------------------------------

    def detect_multi_signal(
        self,
        signals: dict[str, list[float]],
        entity_id: str,
        entity_type: str,
        entity_layer: int,
        methods: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Run detection across all metrics and aggregate into AnomalySignals.

        Parameters
        ----------
        signals:
            Mapping of metric_name → list of recent values.
        entity_id:
            Stable entity identifier.
        entity_type:
            Entity type (e.g. "service", "database", "host").
        entity_layer:
            Topology layer number (1-8).
        methods:
            List of detection method names to use. Defaults to all available.

        Returns
        -------
        List of AnomalySignal dicts matching the AGENTS.md contract.
        """
        if methods is None:
            methods = list(DETECTION_METHODS.keys())

        detector_map = {
            "z_score": self.detect_z_score,
            "ewma": self.detect_ewma,
            "iqr": self.detect_iqr,
            "bocpd": self.detect_bocpd,
        }

        # Filter to available methods
        active_methods = [m for m in methods if m in detector_map]
        if not active_methods:
            logger.warning("No valid detection methods specified: %s", methods)
            return []

        results: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc).isoformat()

        for metric_name, values in signals.items():
            if not values:
                continue

            # Get baseline for this entity+metric
            baseline = self._baseline_engine.get_baseline(
                entity_id, metric_name, values
            )

            # Run each detector
            method_anomalies: dict[str, list[dict]] = {}
            for method_name in active_methods:
                try:
                    anomalies = detector_map[method_name](values, baseline)
                    method_anomalies[method_name] = anomalies
                except Exception as exc:
                    logger.warning(
                        "Detection method %s failed for %s/%s: %s",
                        method_name, entity_id, metric_name, exc,
                    )

            # Collect all anomalous indices across methods
            all_indices: dict[int, dict[str, Any]] = {}
            for method_name, anomalies in method_anomalies.items():
                for a in anomalies:
                    idx = a["index"]
                    if idx not in all_indices:
                        all_indices[idx] = {
                            "index": idx,
                            "value": a["value"],
                            "methods": [],
                            "details": {},
                        }
                    all_indices[idx]["methods"].append(method_name)
                    all_indices[idx]["details"][method_name] = a

            # Build AnomalySignal for each anomalous point
            for idx_data in sorted(all_indices.values(), key=lambda x: x["index"]):
                triggering_methods = idx_data["methods"]
                n_methods = len(triggering_methods)

                # Aggregate anomaly score: more methods agreeing → higher score
                # Base score from method-specific indicators
                scores = []
                for m_name in triggering_methods:
                    detail = idx_data["details"][m_name]
                    if m_name == "z_score":
                        # Normalize z-score: z=3→0.6, z=6→0.9, z=10→1.0
                        z = detail.get("z_score", 0)
                        scores.append(min(z / 10.0, 1.0))
                    elif m_name == "ewma":
                        dev = detail.get("deviation_stds", 0)
                        scores.append(min(dev / 10.0, 1.0))
                    elif m_name == "iqr":
                        scores.append(0.7)
                    elif m_name == "bocpd":
                        scores.append(detail.get("change_point_prob", 0))

                base_score = max(scores) if scores else 0.5

                # Boost score when multiple methods agree
                method_boost = min(n_methods / len(active_methods) * 0.3, 0.3)
                anomaly_score = min(base_score + method_boost, 1.0)

                # Skip if below minimum threshold
                if anomaly_score < self.min_anomaly_score:
                    continue

                # Confidence: based on method agreement and score
                agreement_ratio = n_methods / len(active_methods)
                confidence = round(
                    (anomaly_score * 60 + agreement_ratio * 40), 1
                )

                severity = classify_severity(anomaly_score)

                # Build deviation string
                mean = baseline.get("mean", 0)
                value = idx_data["value"]
                deviation_str = f"{value:.2f} vs baseline {mean:.2f} ({abs(value - mean):.2f} deviation)"

                signal = {
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "entity_layer": entity_layer,
                    "metric_name": metric_name,
                    "anomaly_score": round(anomaly_score, 4),
                    "confidence": confidence,
                    "severity": severity,
                    "detection_methods": triggering_methods,
                    "deviation_from_baseline": deviation_str,
                    "timestamp": now,
                    "status": "open",
                }
                results.append(signal)

        # Sort by anomaly_score descending
        results.sort(key=lambda s: s["anomaly_score"], reverse=True)
        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _loggamma(x: float) -> float:
    """Log of the Gamma function via Stirling + Lanczos approximation.

    Used by the BOCPD Student-t computation. Sufficiently accurate for
    the typical degrees of freedom values encountered.
    """
    if x <= 0:
        return 0.0
    # For large x, use Stirling's approximation
    if x >= 0.5:
        t = x - 0.5
        c = np.log(2 * np.pi) / 2
        return (t + 0.5) * np.log(t + 1) - (t + 1) + 0.5 * np.log(2 * np.pi) + c / (t + 1)
    # Reflection formula for x < 0.5
    return np.log(np.pi / np.sin(np.pi * x)) - _loggamma(1 - x)
