"""
Advanced Analytics: Demand Forecasting

Forecast hourly trip demand using aggregated temporal statistics.
"""

from pathlib import Path
from typing import Dict, Any

import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src.config import DATA_DIR


def run_demand_forecast() -> Dict[str, Any]:
    agg_path = DATA_DIR / "aggregates" / "temporal_hourly_stats.parquet"
    pdf = pd.read_parquet(agg_path)

    # Build a simple time index using year/month/day_of_week/hour
    pdf = pdf.sort_values(
        ["pickup_year", "pickup_month", "pickup_day_of_week", "pickup_hour"]
    )
    pdf["time_index"] = range(len(pdf))

    series = pdf.set_index("time_index")["trip_count"]

    # Lightweight SARIMAX model – enough for coarse forecasts without heavy tuning
    model = SARIMAX(series, order=(1, 1, 1), seasonal_order=(1, 1, 1, 24))
    fit = model.fit(disp=False)
    forecast_horizon = 24
    forecast = fit.get_forecast(steps=forecast_horizon)
    forecast_values = forecast.predicted_mean.tolist()

    insights = [
        {
            "hour_ahead": i + 1,
            "predicted_trips": val,
        }
        for i, val in enumerate(forecast_values)
    ]

    return {
        "analysis_type": "demand_forecast",
        "insights": insights,
        "predictions": insights,
        "recommendations": [
            "Consider increasing driver availability during forecasted peak hours.",
            "Use hourly demand predictions to plan surge pricing windows.",
        ],
        "visualizations": {
            "time_series": {
                "historical": series.tail(7 * 24).tolist(),
                "forecast": forecast_values,
            }
        },
    }


