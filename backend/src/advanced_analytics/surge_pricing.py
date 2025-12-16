"""
Advanced Analytics: Surge Pricing

Identify when and where surge pricing would be effective.
"""

from typing import Dict, Any

import pandas as pd

from src.config import DATA_DIR


def run_surge_pricing() -> Dict[str, Any]:
    temporal_path = DATA_DIR / "aggregates" / "temporal_hourly_stats.parquet"
    geo_path = DATA_DIR / "aggregates" / "geospatial_zone_stats.parquet"

    temporal = pd.read_parquet(temporal_path)
    geo = pd.read_parquet(geo_path)

    # Demand spikes: hours where trip_count is significantly above daily mean
    daily = (
        temporal.groupby(
            ["pickup_year", "pickup_month", "pickup_day_of_week"],
            as_index=False,
        )["trip_count"]
        .agg(["mean", "std"])
        .reset_index()
    )
    temporal = temporal.merge(
        daily,
        on=["pickup_year", "pickup_month", "pickup_day_of_week"],
        how="left",
    )
    temporal["z_score"] = (
        (temporal["trip_count"] - temporal["mean"]) / temporal["std"].replace(0, 1)
    )

    high_demand_hours = temporal[temporal["z_score"] > 1.5].sort_values(
        "z_score", ascending=False
    )

    # Hot zones during those hours
    hot_geo = geo.merge(
        high_demand_hours[
            ["pickup_year", "pickup_month", "pickup_day_of_week", "pickup_hour"]
        ],
        left_on=["pickup_year", "pickup_month"],
        right_on=["pickup_year", "pickup_month"],
        how="inner",
    )

    hot_geo = hot_geo.sort_values("trip_count", ascending=False).head(100)

    return {
        "analysis_type": "surge_pricing",
        "insights": hot_geo.to_dict("records"),
        "predictions": [],
        "recommendations": [
            "Apply surge multipliers during high z-score hours in top-demand zones.",
            "Monitor demand spikes and dynamically adjust driver incentives.",
        ],
        "visualizations": {
            "high_demand_hours": high_demand_hours.to_dict("records"),
        },
    }


