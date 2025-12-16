"""
Advanced Analytics: Revenue Optimization

Identify high-value segments and time windows.
"""

from typing import Dict, Any

import pandas as pd

from src.config import DATA_DIR


def run_revenue_optimization() -> Dict[str, Any]:
    econ_path = DATA_DIR / "aggregates" / "economic_fare_analysis.parquet"

    df = pd.read_parquet(econ_path)

    # Aggregate by time-of-day and day-of-week
    revenue_by_time = (
        df.groupby(["pickup_day_of_week", "pickup_hour"], as_index=False)[
            "total_revenue"
        ]
        .sum()
        .sort_values("total_revenue", ascending=False)
    )

    top_windows = revenue_by_time.head(48).to_dict("records")

    return {
        "analysis_type": "revenue_optimization",
        "insights": top_windows,
        "predictions": [],
        "recommendations": [
            "Allocate more drivers during top revenue windows.",
            "Focus marketing on time slots with strong revenue but moderate demand.",
        ],
        "visualizations": {"revenue_by_time": top_windows},
    }


