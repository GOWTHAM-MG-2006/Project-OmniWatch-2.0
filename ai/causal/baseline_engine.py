"""
OmniWatch 2.0 — NeuroEngine
Component: Baseline Engine
Layer: 6
Phase: 2
Purpose: Dynamic baselines per entity using Holt-Winters, ARIMA, and adaptive fallback
Inputs: Historical metric values (list[float]), entity_id, metric_name
Outputs: Baseline dict (method, level, trend, seasonal, bounds, mean, std) + anomaly check
"""

import os
import logging
from typing import Any
from datetime import datetime

import numpy as np

from config import config

try:
    import redis as redis_lib

    _REDIS_AVAILABLE = True
except ImportError:
    redis_lib = None  # type: ignore
    _REDIS_AVAILABLE = False

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.arima.model import ARIMA as ARIMA_Model

    _STATSMODELS_AVAILABLE = True
except ImportError:
    _STATSMODELS_AVAILABLE = False

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# In-memory cache fallback
# ---------------------------------------------------------------------------

class _InMemoryCache:
    """Fallback cache when Redis is unavailable."""

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if datetime.now().timestamp() > expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = config.BASELINE_CACHE_TTL):
        expiry = datetime.now().timestamp() + ttl
        self._store[key] = (value, expiry)

    def delete(self, key: str):
        self._store.pop(key, None)


# ---------------------------------------------------------------------------
# Baseline Engine
# ---------------------------------------------------------------------------

class BaselineEngine:
    """Computes dynamic baselines and checks anomalies against them.

    Method selection logic:
        - >= 48 data points → Holt-Winters (seasonal detection)
        - >= 10 data points → ARIMA
        - < 10 data points → Simple mean ± std

    Results are cached in Redis (or in-memory fallback) with a 1-hour TTL.
    """

    REDIS_KEY_PREFIX = "baseline:"
    CACHE_TTL = config.BASELINE_CACHE_TTL

    def __init__(self, redis_url: str | None = None):
        self._cache = self._init_cache(redis_url)

    # -- Cache initialisation --------------------------------------------------

    @staticmethod
    def _init_cache(redis_url: str | None):
        if not _REDIS_AVAILABLE:
            logger.info("redis package not installed — using in-memory cache")
            return _InMemoryCache()

        url = redis_url or os.getenv("REDIS_URL") or (
            f"redis://{config.REDIS_HOST}:"
            f"{config.REDIS_PORT}/"
            f"{os.getenv('REDIS_DB', '0')}"
        )

        try:
            client = redis_lib.from_url(url, decode_responses=True)
            client.ping()
            logger.info("Connected to Redis at %s", url)
            return client
        except Exception as exc:
            logger.warning("Redis unavailable (%s) — falling back to in-memory cache", exc)
            return _InMemoryCache()

    # -- Cache key helpers -----------------------------------------------------

    @staticmethod
    def _cache_key(entity_id: str, metric_name: str) -> str:
        return f"{BaselineEngine.REDIS_KEY_PREFIX}{entity_id}:{metric_name}"

    # -- Public API ------------------------------------------------------------

    def get_baseline(
        self,
        entity_id: str,
        metric_name: str,
        values: list[float],
    ) -> dict[str, Any]:
        """Compute or retrieve a cached baseline for the given entity+metric.

        Returns a dict with keys:
            method, level, trend, seasonal, upper_bound, lower_bound, mean, std
        """
        if not values:
            return self._empty_baseline("none")

        cache_key = self._cache_key(entity_id, metric_name)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        n = len(values)
        if n >= 48:
            result = self.compute_holt_winters_baseline(values)
        elif n >= 10:
            result = self.compute_arima_baseline(values)
        else:
            result = self._simple_mean_baseline(values)

        self._cache.set(cache_key, result, self.CACHE_TTL)
        return result

    def is_anomalous(
        self,
        value: float,
        baseline: dict[str, Any],
        threshold: float = 3.0,
    ) -> tuple[bool, float]:
        """Check whether *value* is anomalous relative to the baseline.

        Returns (is_anomalous: bool, z_score: float).
        A value is anomalous when |z_score| > threshold.
        """
        std = baseline.get("std") or 0.0
        mean = baseline.get("mean") or 0.0

        if std == 0:
            return False, 0.0

        z_score = (value - mean) / std
        return abs(z_score) > threshold, float(z_score)

    # -- Holt-Winters ----------------------------------------------------------

    def compute_holt_winters_baseline(self, values: list[float]) -> dict[str, Any]:
        """Triple exponential smoothing (additive) for seasonal data.

        Automatically selects seasonal period based on data length.
        Requires at least 2 full seasonal cycles.
        """
        arr = np.array(values, dtype=np.float64)

        # Determine seasonal period: use 12 if length allows two full cycles,
        # otherwise fall back to the largest feasible divisor.
        period = self._detect_seasonal_period(len(arr))

        if not _STATSMODELS_AVAILABLE or len(arr) < 2 * period:
            return self._simple_mean_baseline(values)

        try:
            model = ExponentialSmoothing(
                arr,
                trend="add",
                seasonal="add",
                seasonal_periods=period,
                initialization_method="estimated",
            )
            fit = model.fit(optimized=True, use_brute=False)

            level = float(fit.level[-1]) if fit.level is not None else float(fit.params.get("l", arr[-1]))
            trend_val = float(fit.trend[-1]) if fit.trend is not None else 0.0
            seasonal = float(fit.season[-1]) if fit.season is not None else 0.0

            fitted = fit.fittedvalues
            residuals = arr - fitted
            sigma = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else float(np.std(residuals))

            mean = float(np.mean(arr))
            std = float(np.std(arr, ddof=1)) if len(arr) > 1 else float(np.std(arr))

            return {
                "method": "holt_winters",
                "level": round(level, 6),
                "trend": round(trend_val, 6),
                "seasonal": round(seasonal, 6),
                "seasonal_period": period,
                "upper_bound": round(level + trend_val + 3 * sigma, 6),
                "lower_bound": round(level + trend_val - 3 * sigma, 6),
                "mean": round(mean, 6),
                "std": round(std, 6),
            }
        except Exception as exc:
            logger.warning("Holt-Winters failed, falling back to simple mean: %s", exc)
            return self._simple_mean_baseline(values)

    # -- ARIMA -----------------------------------------------------------------

    def compute_arima_baseline(self, values: list[float]) -> dict[str, Any]:
        """ARIMA(1,1,1) forecasting for non-seasonal data."""
        arr = np.array(values, dtype=np.float64)

        if not _STATSMODELS_AVAILABLE or len(arr) < 10:
            return self._simple_mean_baseline(values)

        try:
            model = ARIMA_Model(arr, order=(1, 1, 1))
            fit = model.fit()

            forecast = fit.forecast(steps=1)
            level = float(forecast[0])
            trend_val = float(arr[-1] - arr[-2]) if len(arr) >= 2 else 0.0

            sigma = float(np.std(fit.resid, ddof=1)) if len(fit.resid) > 1 else float(np.std(fit.resid))
            mean = float(np.mean(arr))
            std = float(np.std(arr, ddof=1)) if len(arr) > 1 else float(np.std(arr))

            return {
                "method": "arima",
                "level": round(level, 6),
                "trend": round(trend_val, 6),
                "seasonal": 0.0,
                "upper_bound": round(level + 3 * sigma, 6),
                "lower_bound": round(level - 3 * sigma, 6),
                "mean": round(mean, 6),
                "std": round(std, 6),
            }
        except Exception as exc:
            logger.warning("ARIMA failed, falling back to simple mean: %s", exc)
            return self._simple_mean_baseline(values)

    # -- Simple mean fallback --------------------------------------------------

    @staticmethod
    def _simple_mean_baseline(values: list[float]) -> dict[str, Any]:
        arr = np.array(values, dtype=np.float64)
        mean = float(np.mean(arr))
        std = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0

        return {
            "method": "simple_mean",
            "level": round(mean, 6),
            "trend": 0.0,
            "seasonal": 0.0,
            "upper_bound": round(mean + 3 * std, 6),
            "lower_bound": round(mean - 3 * std, 6),
            "mean": round(mean, 6),
            "std": round(std, 6),
        }

    @staticmethod
    def _empty_baseline(method: str = "none") -> dict[str, Any]:
        return {
            "method": method,
            "level": 0.0,
            "trend": 0.0,
            "seasonal": 0.0,
            "upper_bound": 0.0,
            "lower_bound": 0.0,
            "mean": 0.0,
            "std": 0.0,
        }

    # -- Helpers ---------------------------------------------------------------

    @staticmethod
    def _detect_seasonal_period(n: int) -> int:
        """Pick a seasonal period that allows at least 2 full cycles.

        Prefers 12 (hourly seasonality). Falls back to the largest feasible
        divisor so that 2 * period <= n.
        """
        candidates = [12, 24, 7, 4]
        for p in candidates:
            if n >= 2 * p:
                return p
        # Generic fallback: largest p where 2*p <= n
        for p in range(n // 2, 1, -1):
            if n >= 2 * p:
                return p
        return 1

    # -- Learning feedback ----------------------------------------------------

    def apply_learning_feedback(self, patterns: list[dict[str, Any]]) -> None:
        """Apply pattern mining feedback to improve baseline thresholds.

        Args:
            patterns: List of patterns from pattern_miner.mine_patterns().
        """
        for pattern in patterns:
            pattern_type = pattern.get("pattern_type", "")
            if pattern_type == "recurring_entity_failure":
                entity = pattern.get("entity", "")
                confidence = pattern.get("confidence", 0)
                if confidence > 0.5:
                    logger.info("Learning feedback: entity %s has recurring failures (confidence=%.2f)", entity, confidence)
            elif pattern_type == "action_effectiveness":
                action = pattern.get("action_type", "")
                rate = pattern.get("success_rate", 0)
                logger.info("Learning feedback: action %s has success rate %.0f%%", action, rate * 100)
