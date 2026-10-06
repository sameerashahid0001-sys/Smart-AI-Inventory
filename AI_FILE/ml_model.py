"""
Machine Learning Demand Forecasting Module
Uses Random Forest to learn demand patterns from historical inventory data.
"""

import numpy as np
import pandas as pd

from typing import List, Dict, Any

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


class InventoryMLPredictor:
    """
    Machine Learning model for inventory demand forecasting.
    The model learns from historical demand and creates features such as:
    1. Previous demand
    2. Moving averages
    3. Demand trend
    4. Month/period number
    """

    def __init__(self, n_estimators: int = 200):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            random_state=42,
            max_depth=10,
            min_samples_leaf=2
        )

        self.is_trained = False
        self.feature_columns = [
            "lag_1",
            "lag_2",
            "lag_3",
            "moving_avg_3",
            "moving_avg_6",
            "trend",
            "period"
        ]

        self.training_mae = None
        self.training_rmse = None
    # CREATE FEATURES
    def create_features(self, history: List[float]) -> pd.DataFrame:

        if len(history) < 4:
            raise ValueError(
                "At least 4 historical demand periods are required "
                "for machine learning."
            )

        df = pd.DataFrame({
            "demand": history
        })

        # Previous demand values
        df["lag_1"] = df["demand"].shift(1)
        df["lag_2"] = df["demand"].shift(2)
        df["lag_3"] = df["demand"].shift(3)

        # Moving averages
        df["moving_avg_3"] = (
            df["demand"]
            .shift(1)
            .rolling(window=3)
            .mean()
        )

        df["moving_avg_6"] = (
            df["demand"]
            .shift(1)
            .rolling(window=6)
            .mean()
        )

        # Simple demand trend
        df["trend"] = (
            df["demand"].shift(1)
            - df["demand"].shift(2)
        )

        # Time/period number
        df["period"] = np.arange(len(df))

        # Remove rows where lag features are unavailable
        df = df.dropna().reset_index(drop=True)

        return df

    # TRAIN MODEL

    def train(self, history: List[float]) -> Dict[str, Any]:

        history = [
            max(0.0, float(x))
            for x in history
            if x is not None and not np.isnan(float(x))
        ]

        if len(history) < 8:
            return {
                "success": False,
                "message": (
                    "Not enough historical data. "
                    "At least 8 periods are recommended."
                )
            }

        df = self.create_features(history)

        X = df[self.feature_columns]
        y = df["demand"]

        # Time-series split:
        # Older data = training
        # Newer data = testing
        split_index = max(1, int(len(X) * 0.8))

        X_train = X.iloc[:split_index]
        y_train = y.iloc[:split_index]

        X_test = X.iloc[split_index:]
        y_test = y.iloc[split_index:]

        # Train
        self.model.fit(X_train, y_train)

        self.is_trained = True

        # Evaluate
        if len(X_test) > 0:

            predictions = self.model.predict(X_test)

            self.training_mae = float(
                mean_absolute_error(y_test, predictions)
            )

            self.training_rmse = float(
                np.sqrt(
                    mean_squared_error(y_test, predictions)
                )
            )

        return {
            "success": True,
            "training_periods": len(X_train),
            "testing_periods": len(X_test),
            "mae": round(self.training_mae, 2)
            if self.training_mae is not None else None,
            "rmse": round(self.training_rmse, 2)
            if self.training_rmse is not None else None,
            "model": "Random Forest Regressor"
        }
    # FORECAST NEXT PERIOD

    def predict_next(self, history: List[float]) -> float:

        if not self.is_trained:
            result = self.train(history)

            if not result["success"]:
                raise ValueError(result["message"])

        history = [
            max(0.0, float(x))
            for x in history
        ]

        if len(history) < 4:
            raise ValueError(
                "At least 4 historical periods are required."
            )

        # Create features for the next period

        lag_1 = history[-1]
        lag_2 = history[-2]
        lag_3 = history[-3]

        moving_avg_3 = np.mean(history[-3:])

        moving_avg_6 = (
            np.mean(history[-6:])
            if len(history) >= 6
            else np.mean(history)
        )

        trend = history[-1] - history[-2]

        period = len(history)

        X_future = pd.DataFrame([{
            "lag_1": lag_1,
            "lag_2": lag_2,
            "lag_3": lag_3,
            "moving_avg_3": moving_avg_3,
            "moving_avg_6": moving_avg_6,
            "trend": trend,
            "period": period
        }])

        prediction = self.model.predict(
            X_future[self.feature_columns]
        )[0]

        return round(max(0.0, float(prediction)), 2)

    # MULTI-PERIOD FORECAST

    def predict(
        self,
        history: List[float],
        horizon: int = 1
    ) -> Dict[str, Any]:

        result = self.train(history)

        if not result["success"]:
            return {
                "forecast": [],
                "next_period": 0.0,
                "method": "Random Forest ML",
                "error": result["message"]
            }

        working_history = list(history)
        forecasts = []

        for _ in range(horizon):

            prediction = self.predict_next(
                working_history
            )

            forecasts.append(prediction)

            # Add prediction to history so the model
            # can generate the next future period
            working_history.append(prediction)

        return {
            "forecast": forecasts,
            "next_period": forecasts[0]
            if forecasts else 0.0,
            "total_horizon_demand": round(
                sum(forecasts), 2
            ),
            "method": "Random Forest Machine Learning",
            "mae": result["mae"],
            "rmse": result["rmse"],
            "explanation": (
                "Random Forest learned demand patterns "
                "from historical demand, lag values, "
                "moving averages, and demand trend."
            )
        }