"""
Advanced Analytics: Route Optimization

Identify inefficient routes (high duration vs distance) from route aggregates.
"""

from typing import Dict, Any

import pandas as pd

from src.config import DATA_DIR


def run_route_optimization() -> Dict[str, Any]:
    agg_path = DATA_DIR / "aggregates" / "route_pairs_top.parquet"
    pdf = pd.read_parquet(agg_path)

    # Compute efficiency metric: minutes per mile
    pdf["minutes_per_mile"] = pdf["avg_duration"] / pdf["avg_distance"].clip(lower=0.1)

    # Pick worst (slowest) routes with enough volume
    inefficient = (
        pdf[pdf["trip_count"] > 200]
        .sort_values("minutes_per_mile", ascending=False)
        .head(50)
    )

    insights = inefficient.to_dict("records")

    recommendations = [
        "Review traffic patterns for slow routes and adjust suggested paths.",
        "Consider driver guidance to avoid known bottlenecks on the worst routes.",
    ]

    return {
        "analysis_type": "route_optimization",
        "insights": insights,
        "predictions": [],
        "recommendations": recommendations,
        "visualizations": {
            "inefficient_routes": insights,
        },
    }


