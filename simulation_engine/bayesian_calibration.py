"""
OmniWatch 2.0 — SimulaX
Component: Bayesian Calibration Engine
Layer: 8
Phase: 3
Purpose: Auto-tunes simulation model parameters against observed reality using Optuna
Inputs: Simulation predictions vs actual outcomes (from knowledge_base)
Outputs: Calibrated model parameters → Redis
Technology: Optuna
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Any

from config import config

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

logger = logging.getLogger(__name__)

try:
    import optuna
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False
    logger.info("Optuna not installed — using default calibration parameters")


class BayesianCalibrator:
    """Auto-tunes simulation model parameters using Bayesian optimization.

    Compares simulation predictions against actual outcomes to minimize
    prediction error over time.
    """

    PARAMETER_DEFAULTS = {
        "rollback_base_time": 3.0,
        "restart_base_time": 1.0,
        "scale_base_time": 2.0,
        "cascade_probability_factor": 1.0,
        "cpu_risk_threshold": 80.0,
        "memory_risk_threshold": 80.0,
    }

    def __init__(self, redis_host: str | None = None, redis_port: int | None = None, redis_db: int = 3):
        self.redis_host = redis_host or config.REDIS_HOST
        self.redis_port = int(redis_port or config.REDIS_PORT)
        self.redis_db = redis_db
        self._redis = None
        self._memory_store: dict[str, str] = {}
        self._prefix = "ow:calibration:"

    @property
    def conn(self):
        if self._redis is None and HAS_REDIS:
            try:
                self._redis = redis.Redis(
                    host=self.redis_host, port=self.redis_port,
                    db=self.redis_db, decode_responses=True,
                )
                self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    def _store_get(self, key: str) -> str | None:
        if self.conn:
            return self.conn.get(key)
        return self._memory_store.get(key)

    def _store_set(self, key: str, value: str) -> None:
        if self.conn:
            self.conn.set(key, value)
        else:
            self._memory_store[key] = value

    def get_parameters(self) -> dict[str, float]:
        """Get current calibrated parameters."""
        raw = self._store_get(f"{self._prefix}params")
        if raw:
            return json.loads(raw)
        return dict(self.PARAMETER_DEFAULTS)

    def save_parameters(self, params: dict[str, float]) -> None:
        """Save calibrated parameters to Redis."""
        self._store_set(f"{self._prefix}params", json.dumps(params))

    def calibrate(
        self,
        predictions: list[dict[str, Any]],
        actuals: list[dict[str, Any]],
        n_trials: int = 50,
    ) -> dict[str, float]:
        """Run Bayesian calibration to minimize prediction error.

        Args:
            predictions: List of simulation prediction dicts.
            actuals: List of actual outcome dicts (same order as predictions).
            n_trials: Number of Optuna optimization trials.

        Returns:
            Calibrated parameter dict.
        """
        if not HAS_OPTUNA or not predictions:
            return self.get_parameters()

        current_params = self.get_parameters()

        def objective(trial: optuna.Trial) -> float:
            params = {
                "rollback_base_time": trial.suggest_float("rollback_base_time", 1.0, 10.0),
                "restart_base_time": trial.suggest_float("restart_base_time", 0.5, 5.0),
                "scale_base_time": trial.suggest_float("scale_base_time", 1.0, 8.0),
                "cascade_probability_factor": trial.suggest_float("cascade_factor", 0.5, 2.0),
            }

            total_error = 0.0
            for pred, actual in zip(predictions, actuals):
                pred_time = pred.get("recovery_time_minutes", 5)
                actual_time = actual.get("actual_recovery_time_minutes", pred_time)
                total_error += abs(pred_time - actual_time) ** 2

            return (total_error / len(predictions)) ** 0.5

        study = optuna.create_study(direction="minimize")
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

        best = study.best_params
        calibrated = {**current_params, **best}
        self.save_parameters(calibrated)

        logger.info("Calibration complete: best RMSE=%.2f, params=%s", study.best_value, best)
        return calibrated
