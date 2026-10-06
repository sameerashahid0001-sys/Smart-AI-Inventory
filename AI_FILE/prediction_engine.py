"""
Inventory Prediction Engine
Forecasting methods:
1. Simple Moving Average (SMA)
2. Weighted Moving Average / Weighted Mean (WMA)
3. Simple Exponential Smoothing (SES)
4. Holt's Double Exponential Smoothing (Trend-Adjusted)
5. Linear Regression

Also implements:
6. Safety Stock
7. Reorder Point (ROP)
8. Recommended Order Quantity (ROQ)
9. Inventory Risk Metrics
"""

import numpy as np
from typing import List, Dict, Any
from sklearn.linear_model import LinearRegression


def clean_history(history: List[float]) -> List[float]:
    """Clean demand history by removing NaN values and preventing negative demand."""
    result = []
    for x in history:
        try:
            value = float(x)
            if not np.isnan(value):
                result.append(max(0.0, value))
        except (TypeError, ValueError):
            continue
    return result


class MovingAveragePredictor:
    """
    Simple Moving Average (SMA).

    Uses the average of the most recent `window` periods.
    Example:
        Demand = [100, 120, 110]
        Window = 3
        Forecast = (100 + 120 + 110) / 3
    """

    @classmethod
    def predict(
        cls,
        history: List[float],
        horizon: int = 1,
        window: int = 3
    ) -> Dict[str, Any]:

        history = clean_history(history)

        if not history:
            return {
                "forecast": [0.0] * horizon,
                "next_period": 0.0,
                "total_horizon_demand": 0.0,
                "std_dev": 0.0,
                "method": "Simple Moving Average",
                "window": window,
                "formula": "SMA = Sum of recent demand / Number of periods",
                "explanation": "No historical demand data provided."
            }

        window = max(1, min(int(window), len(history)))
        recent = history[-window:]

        # Recursive multi-step forecast.
        forecasts = []
        simulated = list(history)

        for _ in range(horizon):
            value = float(np.mean(simulated[-window:]))
            forecasts.append(round(max(0.0, value), 2))
            simulated.append(value)

        std_dev = float(np.std(history)) if len(history) > 1 else forecasts[0] * 0.15

        return {
            "forecast": forecasts,
            "next_period": forecasts[0],
            "total_horizon_demand": round(sum(forecasts), 2),
            "std_dev": round(std_dev, 2),
            "method": "Simple Moving Average (SMA)",
            "window": window,
            "recent_values": recent,
            "formula": "SMA = Sum of recent demand / Number of periods",
            "explanation": f"Forecast uses the average of the most recent {window} periods."
        }


class WeightedMeanPredictor:
    #Weighted Moving Average / Weighted Mean (WMA).
    #More recent periods receive higher weights.


    @staticmethod
    def calculate_weights(
        n: int,
        weighting_type: str = "linear"
    ) -> np.ndarray:

        if n <= 0:
            return np.array([])

        if n == 1:
            return np.array([1.0])

        if weighting_type == "exponential":
            raw_weights = np.exp(np.linspace(0, 1.5, n))
        elif weighting_type == "recent_heavy":
            raw_weights = np.arange(1, n + 1, dtype=float) ** 1.5
        else:
            raw_weights = np.arange(1, n + 1, dtype=float)

        return raw_weights / np.sum(raw_weights)

    @classmethod
    def predict(
        cls,
        history: List[float],
        horizon: int = 1,
        weighting_type: str = "linear",
        window: int = 3
    ) -> Dict[str, Any]:

        history = clean_history(history)

        if not history:
            return {
                "forecast": [0.0] * horizon,
                "next_period": 0.0,
                "total_horizon_demand": 0.0,
                "weights": [],
                "std_dev": 0.0,
                "method": "Weighted Moving Average",
                "formula": "WMA = Sum(weight x demand) / Sum(weights)",
                "explanation": "No historical demand data provided."
            }

        window = max(1, min(int(window), len(history)))
        recent = history[-window:]

        weights = cls.calculate_weights(window, weighting_type)
        one_step = float(np.sum(np.array(recent) * weights))

        forecasts = []
        simulated = list(history)

        for _ in range(horizon):
            recent_simulated = simulated[-window:]
            w = cls.calculate_weights(len(recent_simulated), weighting_type)
            value = float(np.sum(np.array(recent_simulated) * w))
            forecasts.append(round(max(0.0, value), 2))
            simulated.append(value)

        weight_breakdown = [
            {
                "period": i + 1,
                "demand": recent[i],
                "weight": round(float(weights[i]), 4)
            }
            for i in range(window)
        ]

        std_dev = float(np.std(history)) if len(history) > 1 else one_step * 0.15

        return {
            "forecast": forecasts,
            "next_period": round(one_step, 2),
            "total_horizon_demand": round(sum(forecasts), 2),
            "weights": [round(float(w), 4) for w in weights],
            "weight_breakdown": weight_breakdown,
            "std_dev": round(std_dev, 2),
            "method": "Weighted Moving Average (WMA)",
            "window": window,
            "weighting_type": weighting_type,
            "formula": "WMA = Sum(weight × demand) / Sum(weights)",
            "explanation": (
                f"Forecast uses the most recent {window} periods with "
                f"{weighting_type} weights."
            )
        }


class ExponentialSmoothingPredictor:
    """
    Simple Exponential Smoothing (SES).

    Best for demand with no strong trend or seasonality.
    Alpha controls how strongly the model reacts to recent demand.
    """

    @classmethod
    def predict(
        cls,
        history: List[float],
        horizon: int = 1,
        alpha: float = 0.3
    ) -> Dict[str, Any]:

        history = clean_history(history)
        alpha = min(1.0, max(0.0, float(alpha)))

        if not history:
            return {
                "forecast": [0.0] * horizon,
                "next_period": 0.0,
                "total_horizon_demand": 0.0,
                "std_dev": 0.0,
                "method": "Simple Exponential Smoothing",
                "alpha": alpha,
                "formula": "S_t = αY_t + (1-α)S_(t-1)",
                "explanation": "No historical demand data provided."
            }

        # Initialize smoothed level with first observation.
        level = history[0]

        for value in history[1:]:
            level = alpha * value + (1 - alpha) * level

        forecasts = [round(max(0.0, level), 2)] * horizon
        std_dev = float(np.std(history)) if len(history) > 1 else level * 0.15

        return {
            "forecast": forecasts,
            "next_period": forecasts[0],
            "total_horizon_demand": round(sum(forecasts), 2),
            "std_dev": round(std_dev, 2),
            "final_level": round(level, 2),
            "method": "Simple Exponential Smoothing (SES)",
            "alpha": alpha,
            "formula": "S_t = αY_t + (1-α)S_(t-1)",
            "explanation": (
                f"Smoothed demand using alpha={alpha}. "
                "Higher alpha gives more importance to recent demand."
            )
        }


class HoltWintersPredictor:
    """
    Holt's Double Exponential Smoothing.
    Models both:
    1. Level
    2. Trend
    Useful when demand has a clear upward or downward trend.
    """
    @classmethod
    def predict(
        cls,
        history: List[float],
        horizon: int = 1,
        alpha: float = 0.3,
        beta: float = 0.2
    ) -> Dict[str, Any]:

        history = clean_history(history)
        alpha = min(1.0, max(0.0, float(alpha)))
        beta = min(1.0, max(0.0, float(beta)))

        if not history:
            return {
                "forecast": [0.0] * horizon,
                "next_period": 0.0,
                "total_horizon_demand": 0.0,
                "std_dev": 0.0,
                "method": "Holt's Linear Smoothing",
                "trend": 0.0,
                "level": 0.0
            }

        if len(history) < 2:
            value = history[0]
            return {
                "forecast": [round(value, 2)] * horizon,
                "next_period": round(value, 2),
                "total_horizon_demand": round(value * horizon, 2),
                "std_dev": round(value * 0.15, 2),
                "level": round(value, 2),
                "trend": 0.0,
                "method": "Holt's Linear (Single Point Fallback)",
                "formula": "F_(t+h) = L_t + hT_t"
            }

        level = history[0]
        trend = history[1] - history[0]

        for value in history[1:]:
            previous_level = level
            previous_trend = trend

            level = alpha * value + (1 - alpha) * (
                previous_level + previous_trend
            )

            trend = beta * (level - previous_level) + (
                1 - beta
            ) * previous_trend

        forecasts = []

        for h in range(1, horizon + 1):
            value = max(0.0, level + h * trend)
            forecasts.append(round(value, 2))

        std_dev = float(np.std(history)) if len(history) > 1 else forecasts[0] * 0.15

        return {
            "forecast": forecasts,
            "next_period": forecasts[0],
            "total_horizon_demand": round(sum(forecasts), 2),
            "std_dev": round(std_dev, 2),
            "final_level": round(level, 2),
            "final_trend": round(trend, 2),
            "alpha": alpha,
            "beta": beta,
            "method": "Holt's Double Exponential Smoothing",
            "formula": "F_(t+h) = L_t + hT_t",
            "explanation": (
                f"Modeled level={round(level, 2)} and "
                f"trend={round(trend, 2)} units/period."
            )
        }
class LinearRegressionPredictor:
    """
    Linear Regression Forecasting.
    Fits:
        Demand = intercept + slope x time
    Useful when historical demand has a relatively consistent upward
    or downward trend.
    """

    @classmethod
    def predict(
        cls,
        history: List[float],
        horizon: int = 1
    ) -> Dict[str, Any]:

        history = clean_history(history)

        if not history:
            return {
                "forecast": [0.0] * horizon,
                "next_period": 0.0,
                "total_horizon_demand": 0.0,
                "std_dev": 0.0,
                "method": "Linear Regression",
                "slope": 0.0,
                "intercept": 0.0,
                "r_squared": 0.0,
                "formula": "Demand = intercept + slope × time",
                "explanation": "No historical demand data provided."
            }

        if len(history) == 1:
            value = history[0]
            return {
                "forecast": [round(value, 2)] * horizon,
                "next_period": round(value, 2),
                "total_horizon_demand": round(value * horizon, 2),
                "std_dev": round(value * 0.15, 2),
                "method": "Linear Regression (Single Point Fallback)",
                "slope": 0.0,
                "intercept": round(value, 2),
                "r_squared": 1.0,
                "formula": "Demand = intercept + slope × time"
            }

        x = np.arange(1, len(history) + 1).reshape(-1, 1)
        y = np.array(history)

        model = LinearRegression()
        model.fit(x, y)

        future_x = np.arange(
            len(history) + 1,
            len(history) + horizon + 1
        ).reshape(-1, 1)

        predictions = model.predict(future_x)
        predictions = np.maximum(predictions, 0.0)

        forecasts = [round(float(x), 2) for x in predictions]

        std_dev = float(np.std(history)) if len(history) > 1 else forecasts[0] * 0.15

        return {
            "forecast": forecasts,
            "next_period": forecasts[0],
            "total_horizon_demand": round(sum(forecasts), 2),
            "std_dev": round(std_dev, 2),
            "slope": round(float(model.coef_[0]), 4),
            "intercept": round(float(model.intercept_), 2),
            "r_squared": round(float(model.score(x, y)), 4),
            "method": "Linear Regression",
            "formula": "Demand = intercept + slope × time",
            "explanation": (
                f"Regression slope={round(float(model.coef_[0]), 4)}. "
                f"R²={round(float(model.score(x, y)), 4)}."
            )
        }


class InventoryForecastEngine:
    """
    Runs all forecasting methods and provides a single interface.
    Available methods:
        1. moving_average
        2. weighted_mean
        3. exponential_smoothing
        4. holt
        5. linear_regression
        6. all
    """

    METHODS = {
        "moving_average": MovingAveragePredictor,
        "weighted_mean": WeightedMeanPredictor,
        "exponential_smoothing": ExponentialSmoothingPredictor,
        "holt": HoltWintersPredictor,
        "linear_regression": LinearRegressionPredictor,
    }

    @classmethod
    def predict(
        cls,
        history: List[float],
        method: str = "weighted_mean",
        horizon: int = 1,
        window: int = 3,
        weighting_type: str = "linear",
        alpha: float = 0.3,
        beta: float = 0.2
    ) -> Dict[str, Any]:

        method = method.lower().strip()

        if method == "all":
            return cls.predict_all(
                history=history,
                horizon=horizon,
                window=window,
                weighting_type=weighting_type,
                alpha=alpha,
                beta=beta
            )

        if method not in cls.METHODS:
            raise ValueError(
                f"Unknown method '{method}'. "
                f"Choose from: {list(cls.METHODS.keys())} or 'all'."
            )

        predictor = cls.METHODS[method]

        if method == "moving_average":
            return predictor.predict(
                history, horizon, window
            )

        if method == "weighted_mean":
            return predictor.predict(
                history, horizon, weighting_type, window
            )

        if method == "exponential_smoothing":
            return predictor.predict(
                history, horizon, alpha
            )

        if method == "holt":
            return predictor.predict(
                history, horizon, alpha, beta
            )

        return predictor.predict(
            history, horizon
        )

    @classmethod
    def predict_all(
        cls,
        history: List[float],
        horizon: int = 1,
        window: int = 3,
        weighting_type: str = "linear",
        alpha: float = 0.3,
        beta: float = 0.2
    ) -> Dict[str, Any]:

        results = {}

        results["moving_average"] = MovingAveragePredictor.predict(
            history, horizon, window
        )

        results["weighted_mean"] = WeightedMeanPredictor.predict(
            history, horizon, weighting_type, window
        )

        results["exponential_smoothing"] = ExponentialSmoothingPredictor.predict(
            history, horizon, alpha
        )

        results["holt"] = HoltWintersPredictor.predict(
            history, horizon, alpha, beta
        )

        results["linear_regression"] = LinearRegressionPredictor.predict(
            history, horizon
        )

        return results


class InventoryOptimizationEngine:
    """
    Computes:
    1. Safety Stock
    2. Reorder Point (ROP)
    3. Recommended Order Quantity (ROQ)
    4. Days of Inventory (DOI)
    5. Inventory Risk
    6. Financial estimates
    """
    SERVICE_LEVEL_Z = {
        0.80: 0.84,
        0.85: 1.04,
        0.90: 1.28,
        0.95: 1.645,
        0.98: 2.05,
        0.99: 2.33
    }
    @classmethod
    def get_z_score(cls, service_level: float) -> float:
        closest_key = min(
            cls.SERVICE_LEVEL_Z.keys(),
            key=lambda k: abs(k - service_level)
        )
        return cls.SERVICE_LEVEL_Z[closest_key]
    @classmethod
    def calculate_metrics(
        cls,
        current_stock: float,
        predicted_demand_per_month: float,
        historical_std_dev: float,
        lead_time_days: float = 14.0,
        service_level: float = 0.95,
        unit_cost: float = 10.0,
        unit_price: float = 20.0,
        holding_cost_rate: float = 0.20
    ) -> Dict[str, Any]:
        daily_demand = max(
            0.01,
            predicted_demand_per_month / 30.0
        )
        daily_std = max(
            0.01,
            historical_std_dev / np.sqrt(30.0)
        )
        lead_time_days = max(1.0, float(lead_time_days))
        z_val = cls.get_z_score(service_level)
        lead_time_demand = daily_demand * lead_time_days
        safety_stock = z_val * np.sqrt(lead_time_days) * daily_std
        safety_stock = max(1.0, safety_stock)
        reorder_point = lead_time_demand + safety_stock
        days_of_inventory = (
            current_stock / daily_demand
            if daily_demand > 0
            else 999.0
        )
        needs_reorder = bool(current_stock <= reorder_point)
        target_stock = reorder_point + predicted_demand_per_month
        if needs_reorder:
            recommended_order_qty = max(
                0.0,
                float(target_stock - current_stock)
            )
        else:
            recommended_order_qty = 0.0
        recommended_order_qty = float(
            np.ceil(recommended_order_qty)
        )
        reorder_point = float(round(reorder_point, 1))
        safety_stock = float(round(safety_stock, 1))
        lead_time_demand = float(round(lead_time_demand, 1))
        if current_stock == 0:
            status = "Stockout (Out of Stock)"
            risk_level = "CRITICAL"
            status_badge = "critical"
        elif current_stock <= safety_stock:
            status = "Critical Low (Breaching Safety Stock)"
            risk_level = "HIGH"
            status_badge = "high"
        elif current_stock <= reorder_point:
            status = "Reorder Needed (Below ROP)"
            risk_level = "MEDIUM"
            status_badge = "medium"
        elif days_of_inventory > 90:
            status = "Overstocked (Excess Capital)"
            risk_level = "OVERSTOCK"
            status_badge = "overstock"
        else:
            status = "Healthy / Optimal Stock"
            risk_level = "HEALTHY"
            status_badge = "healthy"
        stock_value = round(
            current_stock * unit_cost,
            2
        )
        reorder_investment = round(
            recommended_order_qty * unit_cost,
            2
        )
        annual_holding_cost = round(
            stock_value * holding_cost_rate,
            2
        )
        return {
            "daily_demand": round(daily_demand, 2),
            "lead_time_days": round(lead_time_days, 1),
            "lead_time_demand": lead_time_demand,
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "days_of_inventory": round(days_of_inventory, 1),
            "needs_reorder": needs_reorder,
            "recommended_order_qty": recommended_order_qty,
            "status": status,
            "risk_level": risk_level,
            "status_badge": status_badge,
            "service_level_pct": int(service_level * 100),
            "stock_value": stock_value,
            "reorder_investment": reorder_investment,
            "annual_holding_cost": annual_holding_cost,
            "unit_cost": round(unit_cost, 2),
            "unit_price": round(unit_price, 2)
        }
# Example usage
if __name__ == "__main__":
    demand_history = [
        120, 135, 128, 145, 150,
        142, 160, 155, 170, 180
    ]
    # Run one method:
    result = InventoryForecastEngine.predict(
        history=demand_history,
        method="weighted_mean",
        horizon=3,
        window=3
    )
    print("\nWeighted Moving Average:")
    print(result)
    # Run every forecasting method:
    all_results = InventoryForecastEngine.predict_all(
        history=demand_history,
        horizon=3,
        window=3,
        weighting_type="linear",
        alpha=0.3,
        beta=0.2
    )
    print("\nAll Forecasting Methods:")
    for method_name, result in all_results.items():
        print(
            f"{method_name}: "
            f"next={result['next_period']}, "
            f"forecast={result['forecast']}"
        )
    # Example inventory optimization:
    optimization = InventoryOptimizationEngine.calculate_metrics(
        current_stock=500,
        predicted_demand_per_month=result["next_period"],
        historical_std_dev=result["std_dev"],
        lead_time_days=14,
        service_level=0.95,
        unit_cost=10,
        unit_price=20
    )
    print("\nInventory Optimization:")
    print(optimization)
