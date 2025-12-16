"""
Advanced Analytics: Anomaly Detection

Detect unusual patterns in demand, routes, and fares.
"""

from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.config import DATA_DIR


def run_anomaly_detection() -> Dict[str, Any]:
    temporal_path = DATA_DIR / "aggregates" / "temporal_hourly_stats.parquet"
    route_path = DATA_DIR / "aggregates" / "route_pairs_top.parquet"

    temporal = pd.read_parquet(temporal_path)
    route = pd.read_parquet(route_path)

    # Demand anomalies based on trip_count and avg_fare
    temp_features = temporal[["trip_count", "avg_fare"]].to_numpy()
    iso_temp = IsolationForest(contamination=0.01, random_state=42)
    temp_scores = iso_temp.fit_predict(temp_features)
    temporal["anomaly"] = temp_scores == -1
    demand_anomalies = temporal[temporal["anomaly"]].to_dict("records")

    # Route anomalies based on avg_distance vs avg_duration
    route_features = route[["avg_distance", "avg_duration"]].to_numpy()
    iso_route = IsolationForest(contamination=0.01, random_state=42)
    route_scores = iso_route.fit_predict(route_features)
    route["anomaly"] = route_scores == -1
    route_anomalies = route[route["anomaly"]].to_dict("records")

    insights = {
        "demand_anomalies": demand_anomalies,
        "route_anomalies": route_anomalies,
    }

    return {
        "analysis_type": "anomaly_detection",
        "insights": insights,
        "predictions": [],
        "recommendations": [
            "Investigate demand spikes and dips flagged as anomalies.",
            "Review anomalous routes for potential fraud or data issues.",
        ],
        "visualizations": insights,
    }


