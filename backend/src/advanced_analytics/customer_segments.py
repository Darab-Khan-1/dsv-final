"""
Advanced Analytics: Customer Segmentation

Segment customers using aggregate economic and tip behavior data.
"""

from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from src.config import DATA_DIR


def run_customer_segments() -> Dict[str, Any]:
    econ_path = DATA_DIR / "aggregates" / "economic_fare_analysis.parquet"
    tip_path = DATA_DIR / "aggregates" / "tip_behavior_analysis.parquet"

    econ = pd.read_parquet(econ_path)
    tip = pd.read_parquet(tip_path)

    df = econ.merge(
        tip,
        on=["payment_type", "pickup_hour", "distance_bucket"],
        how="left",
        suffixes=("_econ", "_tip"),
    ).fillna(0)

    features = df[
        [
            "avg_fare",
            "avg_tip",
            "tip_percentage",
            "total_revenue",
            "high_tipper_rate",
            "no_tip_rate",
        ]
    ].to_numpy()

    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features)
    df["segment"] = labels

    segment_summary = (
        df.groupby("segment")
        .agg(
            avg_fare=("avg_fare", "mean"),
            avg_tip=("avg_tip", "mean"),
            tip_percentage=("tip_percentage", "mean"),
            total_revenue=("total_revenue", "sum"),
            high_tipper_rate=("high_tipper_rate", "mean"),
            no_tip_rate=("no_tip_rate", "mean"),
        )
        .reset_index()
        .to_dict("records")
    )

    return {
        "analysis_type": "customer_segments",
        "insights": segment_summary,
        "predictions": [],
        "recommendations": [
            "Design targeted promotions for high-value, high-tip segments.",
            "Offer discounts or loyalty rewards to convert low-tip segments.",
        ],
        "visualizations": {"segment_summary": segment_summary},
    }


