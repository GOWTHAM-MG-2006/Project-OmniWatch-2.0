"""
OmniWatch 2.0 — NeuroEngine
Component: LSTMForecaster
Layer: 6
Phase: 2
Purpose: Non-linear pattern forecasting using PyTorch LSTM with EWMA fallback
Inputs: Timestamps, metric values, entity_id, metric_name, forecast horizons
Outputs: Multi-horizon forecasts with confidence intervals
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.info("PyTorch not installed — using statistical EWMA fallback")


if TORCH_AVAILABLE:
    class SimpleLSTM(nn.Module):
        """Minimal LSTM forecaster for single-variable time series."""

        def __init__(self, input_size: int = 1, hidden_size: int = 32, num_layers: int = 2):
            super().__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_size, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1, :])


class LSTMForecaster:
    """Forecasts metric values using LSTM when PyTorch is available, with EWMA fallback."""

    DEFAULT_HORIZONS = [60, 1440, 10080]
    LOOKBACK = 24  # window size for input sequences
    EPOCHS = 50
    HIDDEN_SIZE = 32
    MIN_PER_STEP = 5.0

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

        if len(values) < self.LOOKBACK:
            return self._forecast_statistical(
                timestamps, values, entity_id, metric_name, horizons
            )

        if TORCH_AVAILABLE:
            try:
                return self._forecast_with_torch(
                    timestamps, values, entity_id, metric_name, horizons
                )
            except Exception as e:
                logger.warning("LSTM failed (%s), falling back to EWMA", e)

        return self._forecast_statistical(
            timestamps, values, entity_id, metric_name, horizons
        )

    def _forecast_with_torch(
        self,
        timestamps: list[str],
        values: list[float],
        entity_id: str,
        metric_name: str,
        horizons: list[int],
    ) -> dict:
        arr = np.array(values, dtype=float)
        n = len(arr)

        # Normalize
        mu, sigma = arr.mean(), arr.std()
        sigma = sigma if sigma > 0 else 1.0
        normed = (arr - mu) / sigma

        # Build sequences
        lookback = min(self.LOOKBACK, n - 1)
        X, y = [], []
        for i in range(lookback, n):
            X.append(normed[i - lookback : i])
            y.append(normed[i])

        X = torch.FloatTensor(np.array(X)).unsqueeze(-1)
        y = torch.FloatTensor(np.array(y)).unsqueeze(-1)

        # Train
        model = SimpleLSTM(input_size=1, hidden_size=self.HIDDEN_SIZE)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
        loss_fn = nn.MSELoss()

        model.train()
        for _ in range(self.EPOCHS):
            optimizer.zero_grad()
            pred = model(X)
            loss = loss_fn(pred, y)
            loss.backward()
            optimizer.step()

        # Predict iteratively
        model.eval()
        with torch.no_grad():
            input_seq = torch.FloatTensor(normed[-lookback:]).unsqueeze(0).unsqueeze(-1)
            preds_normed = []
            for _ in range(max(horizons) // int(self.MIN_PER_STEP)):
                next_val = model(input_seq)
                preds_normed.append(next_val.item())
                input_seq = torch.cat(
                    [input_seq[:, 1:, :], next_val.unsqueeze(1)], dim=1
                )

        # Denormalize
        preds = np.array(preds_normed) * sigma + mu

        # Residual std for confidence bounds
        residuals = arr[-lookback:] - np.append(arr[-lookback + 1 :], preds[:lookback])
        residual_std = float(np.std(residuals)) if len(residuals) > 1 else sigma * 0.1

        ts_base = datetime.fromisoformat(timestamps[-1].replace("Z", "+00:00").replace("+00:00", ""))
        steps_per_min = self.MIN_PER_STEP
        horizons_dict = {}

        for h in horizons:
            idx = min(int(h / steps_per_min), len(preds) - 1)
            pred_val = float(preds[idx])
            margin = residual_std * 1.96 if residual_std > 0 else abs(pred_val * 0.05)

            horizons_dict[f"{h}min"] = {
                "predicted_value": round(pred_val, 2),
                "lower_bound": round(pred_val - margin, 2),
                "upper_bound": round(pred_val + margin, 2),
                "timestamp": (ts_base + timedelta(minutes=h)).isoformat(),
            }

        return {
            "entity_id": entity_id,
            "metric_name": metric_name,
            "method": "lstm",
            "horizons": horizons_dict,
            "data_points_used": n,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _forecast_statistical(
        self,
        timestamps: list[str],
        values: list[float],
        entity_id: str,
        metric_name: str,
        horizons: list[int],
    ) -> dict:
        arr = np.array(values, dtype=float)
        n = len(arr)
        mu = float(arr.mean())
        std = float(arr.std())

        # EWMA with optimal alpha
        if n >= 2:
            alphas = [0.1, 0.2, 0.3, 0.5]
            best_alpha = 0.3
            best_mse = float("inf")
            for alpha in alphas:
                ewma = np.zeros(n)
                ewma[0] = arr[0]
                for i in range(1, n):
                    ewma[i] = alpha * arr[i] + (1 - alpha) * ewma[i - 1]
                mse = float(np.mean((arr - ewma) ** 2))
                if mse < best_mse:
                    best_mse = mse
                    best_alpha = alpha

            # Forecast with EWMA
            last_ewma = mu
            for v in arr[-10:]:
                last_ewma = best_alpha * v + (1 - best_alpha) * last_ewma
        else:
            last_ewma = mu

        ts_base = datetime.fromisoformat(timestamps[-1].replace("Z", "+00:00").replace("+00:00", ""))
        margin = std * 1.96 if std > 0 else abs(mu * 0.05)
        horizons_dict = {}

        for h in horizons:
            horizons_dict[f"{h}min"] = {
                "predicted_value": round(last_ewma, 2),
                "lower_bound": round(last_ewma - margin, 2),
                "upper_bound": round(last_ewma + margin, 2),
                "timestamp": (ts_base + timedelta(minutes=h)).isoformat(),
            }

        return {
            "entity_id": entity_id,
            "metric_name": metric_name,
            "method": "ewma",
            "horizons": horizons_dict,
            "data_points_used": n,
            "generated_at": datetime.utcnow().isoformat(),
        }
