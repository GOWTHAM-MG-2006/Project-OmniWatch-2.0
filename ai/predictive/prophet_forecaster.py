"""
OmniWatch 2.0 — NeuroEngine
Component: ProphetForecaster
Layer: 6
Phase: 2
Purpose: Seasonality-aware time-series forecasting using Facebook Prophet with linear fallback
Inputs: Timestamps, metric values, entity_id, metric_name, forecast horizons
Outputs: Multi-horizon forecasts with confidence intervals
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.info("Prophet not installed — using linear extrapolation fallback")


class ProphetForecaster:
    """Forecasts metric values using Prophet when available, with statistical fallback."""

    DEFAULT_HORIZONS = [60, 1440, 10080]  # minutes

    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level

    def forecast(
        self,
        timestamps: list[str],
        values: list[float],
        entity_id: str,
        metric_name: str,
        horizons: Optional[list[int]] = None,
    ) -> dict:
        if horizons is None:
            horizons = self.DEFAULT_HORIZONS

        if len(timestamps) < 5 or len(values) < 5:
            return self._build_result(
                entity_id, metric_name, horizons,
                method="simple_mean",
                predicted=float(np.mean(values)) if values else 0.0,
                std=float(np.std(values)) if values else 0.0,
                data_points=len(values),
                ts_base=timestamps[-1] if timestamps else datetime.utcnow().isoformat(),
            )

        if PROPHET_AVAILABLE:
            try:
                return self._forecast_with_prophet(
                    timestamps, values, entity_id, metric_name, horizons
                )
            except Exception as e:
                logger.warning("Prophet failed (%s), falling back to linear extrapolation", e)

        return self._forecast_fallback(
            timestamps, values, entity_id, metric_name, horizons
        )

    def _forecast_with_prophet(
        self,
        timestamps: list[str],
        values: list[float],
        entity_id: str,
        metric_name: str,
        horizons: list[int],
    ) -> dict:
        import pandas as pd

        df = pd.DataFrame({"ds": pd.to_datetime(timestamps), "y": values})

        model = Prophet(
            interval_width=self.confidence_level,
            daily_seasonality=True if len(values) >= 48 else False,
            weekly_seasonality=True if len(values) >= 168 else False,
            yearly_seasonality=False,
        )
        model.fit(df)

        future = model.make_future_dataframe(periods=max(horizons) // 5, freq="5min")
        pred = model.predict(future)

        ts_base = datetime.fromisoformat(timestamps[-1].replace("Z", "+00:00").replace("+00:00", ""))
        horizons_dict = {}

        for h in horizons:
            target = ts_base + timedelta(minutes=h)
            pred_row = pred[pred["ds"] >= target].iloc[0] if len(pred[pred["ds"] >= target]) > 0 else pred.iloc[-1]
            horizons_dict[f"{h}min"] = {
                "predicted_value": round(float(pred_row["yhat"]), 2),
                "lower_bound": round(float(pred_row["yhat_lower"]), 2),
                "upper_bound": round(float(pred_row["yhat_upper"]), 2),
                "timestamp": target.isoformat(),
            }

        return {
            "entity_id": entity_id,
            "metric_name": metric_name,
            "method": "prophet",
            "horizons": horizons_dict,
            "data_points_used": len(values),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _forecast_fallback(
        self,
        timestamps: list[str],
        values: list[float],
        entity_id: str,
        metric_name: str,
        horizons: list[int],
    ) -> dict:
        arr = np.array(values, dtype=float)
        n = len(arr)
        std = float(np.std(arr))

        # Linear regression for trend
        x = np.arange(n, dtype=float)
        slope, intercept = np.polyfit(x, arr, 1)

        # Seasonality: dominant Fourier component
        if n >= 12:
            fft_vals = np.fft.rfft(arr - arr.mean())
            magnitudes = np.abs(fft_vals[1:])
            if len(magnitudes) > 0:
                dominant_freq = int(np.argmax(magnitudes)) + 1
                period_samples = n / dominant_freq
            else:
                period_samples = n
        else:
            period_samples = n

        ts_base = datetime.fromisoformat(timestamps[-1].replace("Z", "+00:00").replace("+00:00", ""))
        min_per_step = 5.0
        horizons_dict = {}

        for h in horizons:
            future_idx = n + h / min_per_step
            trend_pred = slope * future_idx + intercept

            if period_samples > 0 and n >= 12:
                phase = 2 * np.pi * future_idx / period_samples
                amp = std * 0.5 if std > 0 else 0.0
                seasonal = amp * np.sin(phase)
            else:
                seasonal = 0.0

            predicted = float(trend_pred + seasonal)
            margin = std * 1.96 if std > 0 else abs(predicted * 0.05)

            horizons_dict[f"{h}min"] = {
                "predicted_value": round(predicted, 2),
                "lower_bound": round(predicted - margin, 2),
                "upper_bound": round(predicted + margin, 2),
                "timestamp": (ts_base + timedelta(minutes=h)).isoformat(),
            }

        return {
            "entity_id": entity_id,
            "metric_name": metric_name,
            "method": "linear_extrapolation",
            "horizons": horizons_dict,
            "data_points_used": n,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _build_result(
        self,
        entity_id: str,
        metric_name: str,
        horizons: list[int],
        method: str,
        predicted: float,
        std: float,
        data_points: int,
        ts_base: str,
    ) -> dict:
        ts = datetime.fromisoformat(ts_base.replace("Z", "+00:00").replace("+00:00", ""))
        margin = std * 1.96 if std > 0 else abs(predicted * 0.05)
        horizons_dict = {}
        for h in horizons:
            horizons_dict[f"{h}min"] = {
                "predicted_value": round(predicted, 2),
                "lower_bound": round(predicted - margin, 2),
                "upper_bound": round(predicted + margin, 2),
                "timestamp": (ts + timedelta(minutes=h)).isoformat(),
            }

        return {
            "entity_id": entity_id,
            "metric_name": metric_name,
            "method": method,
            "horizons": horizons_dict,
            "data_points_used": data_points,
            "generated_at": datetime.utcnow().isoformat(),
        }
