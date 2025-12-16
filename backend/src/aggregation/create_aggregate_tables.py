"""
Phase 1: Create Aggregated Parquet Tables

This module reads the fully cleaned NYC taxi dataset and writes a set of
small, pre-aggregated Parquet tables that can be queried efficiently
by the API and advanced analytics layers.
"""

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    avg,
    col,
    count,
    desc,
    expr,
    max as spark_max,
    min as spark_min,
    stddev,
    sum as spark_sum,
    when,
    sum as spark_sum,
    when,
)

from src.config import PROCESSED_DATA_DIR, DATA_DIR
from src.utils.spark_utils import create_spark_session, stop_spark_session


AGGREGATES_DIR = DATA_DIR / "aggregates"


def _ensure_output_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def create_temporal_hourly_stats(df: DataFrame, output_path: Path) -> None:
    """
    Hourly temporal patterns with fine-grained filtering capability.

    Dimensions:
        pickup_year, pickup_month, pickup_day_of_week, pickup_hour
    Metrics:
        trip_count, avg_fare, avg_distance, avg_duration,
        total_revenue, avg_tip, avg_passenger_count,
        median_fare, median_distance
    """
    agg_df = (
        df.groupBy(
            "pickup_year",
            "pickup_month",
            "pickup_day_of_week",
            "pickup_hour",
        )
        .agg(
            count("*").alias("trip_count"),
            avg("fare_amount").alias("avg_fare"),
            avg("trip_distance").alias("avg_distance"),
            avg("trip_duration_minutes").alias("avg_duration"),
            spark_sum("fare_amount").alias("total_revenue"),
            avg("tip_amount").alias("avg_tip"),
            avg("passenger_count").alias("avg_passenger_count"),
            expr("percentile_approx(fare_amount, 0.5)").alias("median_fare"),
            expr("percentile_approx(trip_distance, 0.5)").alias("median_distance"),
        )
        .orderBy("pickup_year", "pickup_month", "pickup_day_of_week", "pickup_hour")
    )

    _ensure_output_dir(output_path)
    agg_df.write.mode("overwrite").parquet(str(output_path))


def create_geospatial_zone_stats(df: DataFrame, output_path: Path) -> None:
    """
    Zone-level pickup/dropoff patterns.

    Uses the 2-decimal degree grids already created during cleaning.

    Dimensions:
        pickup_lat_grid, pickup_lon_grid,
        dropoff_lat_grid, dropoff_lon_grid,
        pickup_year, pickup_month, hour_bucket
    """
    agg_df = (
        df.withColumn(
            "hour_bucket",
            when(col("pickup_hour").between(6, 11), "morning")
            .when(col("pickup_hour").between(12, 17), "afternoon")
            .when(col("pickup_hour").between(18, 22), "evening")
            .otherwise("night"),
        )
        .groupBy(
            "pickup_lat_grid",
            "pickup_lon_grid",
            "dropoff_lat_grid",
            "dropoff_lon_grid",
            "pickup_year",
            "pickup_month",
            "hour_bucket",
        )
        .agg(
            count("*").alias("trip_count"),
            avg("fare_amount").alias("avg_fare"),
            avg("trip_distance").alias("avg_distance"),
            avg("trip_duration_minutes").alias("avg_duration"),
        )
    )

    _ensure_output_dir(output_path)
    agg_df.write.mode("overwrite").parquet(str(output_path))


def create_route_pairs_top(
    df: DataFrame, output_path: Path, min_trips: int = 100
) -> None:
    """
    Most popular origin-destination pairs.

    Dimensions:
        pickup_lat_grid, pickup_lon_grid,
        dropoff_lat_grid, dropoff_lon_grid,
        pickup_year, pickup_month
    """
    agg_df = (
        df.groupBy(
            "pickup_lat_grid",
            "pickup_lon_grid",
            "dropoff_lat_grid",
            "dropoff_lon_grid",
            "pickup_year",
            "pickup_month",
        )
        .agg(
            count("*").alias("trip_count"),
            avg("fare_amount").alias("avg_fare"),
            avg("trip_distance").alias("avg_distance"),
            avg("trip_duration_minutes").alias("avg_duration"),
            spark_sum(
                when(col("pickup_day_of_week").isin(1, 7), 1).otherwise(0)
            ).alias("trip_count_weekend"),
            spark_sum(
                when(~col("pickup_day_of_week").isin(1, 7), 1).otherwise(0)
            ).alias("trip_count_weekday"),
        )
        .filter(col("trip_count") >= min_trips)
        .orderBy(desc("trip_count"))
    )

    _ensure_output_dir(output_path)
    agg_df.write.mode("overwrite").parquet(str(output_path))


def create_economic_fare_analysis(df: DataFrame, output_path: Path) -> None:
    """
    Fare and revenue patterns across segments.

    Buckets are derived from trip_distance, trip_duration_minutes and pickup_hour.
    """
    agg_df = (
        df.withColumn(
            "distance_bucket",
            when(col("trip_distance") < 1, "0-1mi")
            .when(col("trip_distance") < 3, "1-3mi")
            .when(col("trip_distance") < 5, "3-5mi")
            .when(col("trip_distance") < 10, "5-10mi")
            .otherwise("10+mi"),
        )
        .withColumn(
            "duration_bucket",
            when(col("trip_duration_minutes") < 10, "0-10min")
            .when(col("trip_duration_minutes") < 20, "10-20min")
            .when(col("trip_duration_minutes") < 40, "20-40min")
            .otherwise("40+min"),
        )
        .groupBy(
            "distance_bucket",
            "duration_bucket",
            "pickup_hour",
            "pickup_day_of_week",
            "payment_type",
        )
        .agg(
            count("*").alias("trip_count"),
            avg("fare_amount").alias("avg_fare"),
            avg("tip_amount").alias("avg_tip"),
            (avg("tip_amount") / avg("fare_amount") * 100).alias("tip_percentage"),
            spark_sum("fare_amount").alias("total_revenue"),
            (avg("fare_amount") / avg("trip_distance")).alias("fare_per_mile"),
            (
                avg("fare_amount") / avg("trip_duration_minutes")
            ).alias("fare_per_minute"),
        )
    )

    _ensure_output_dir(output_path)
    agg_df.write.mode("overwrite").parquet(str(output_path))


def create_tip_behavior_analysis(df: DataFrame, output_path: Path) -> None:
    """
    Detailed tip analysis across dimensions.
    """
    agg_df = (
        df.withColumn(
            "distance_bucket",
            when(col("trip_distance") < 2, "short")
            .when(col("trip_distance") < 5, "medium")
            .otherwise("long"),
        )
        .groupBy(
            "payment_type",
            "pickup_hour",
            "distance_bucket",
            "passenger_count",
        )
        .agg(
            count("*").alias("trip_count"),
            avg("tip_amount").alias("avg_tip"),
            expr("percentile_approx(tip_amount, 0.5)").alias("median_tip"),
            (avg("tip_amount") / avg("fare_amount") * 100).alias("tip_percentage"),
            (
                spark_sum(
                    when(col("tip_amount") / col("fare_amount") > 0.25, 1).otherwise(0)
                )
                / count("*")
                * 100
            ).alias("high_tipper_rate"),
            (
                spark_sum(when(col("tip_amount") == 0, 1).otherwise(0))
                / count("*")
                * 100
            ).alias("no_tip_rate"),
        )
    )

    _ensure_output_dir(output_path)
    agg_df.write.mode("overwrite").parquet(str(output_path))


def _with_airport_flags(df: DataFrame) -> DataFrame:
    """
    Add simple boolean / label columns to identify airport trips.

    Uses coarse bounding boxes around airports; this is sufficient for
    aggregate-level analysis and avoids expensive UDFs.
    """
    from src.config import AIRPORT_COORDINATES

    jfk = AIRPORT_COORDINATES["JFK"]
    lga = AIRPORT_COORDINATES["LGA"]
    ewr = AIRPORT_COORDINATES["EWR"]

    def _airport_condition(lat_col: str, lon_col: str, cfg: dict):
        return (
            (col(lat_col) >= cfg["lat"] - cfg["radius_miles"] * 0.02)
            & (col(lat_col) <= cfg["lat"] + cfg["radius_miles"] * 0.02)
            & (col(lon_col) >= cfg["lon"] - cfg["radius_miles"] * 0.02)
            & (col(lon_col) <= cfg["lon"] + cfg["radius_miles"] * 0.02)
        )

    df = df.withColumn(
        "pickup_airport",
        when(_airport_condition("pickup_latitude", "pickup_longitude", jfk), "JFK")
        .when(_airport_condition("pickup_latitude", "pickup_longitude", lga), "LGA")
        .when(_airport_condition("pickup_latitude", "pickup_longitude", ewr), "EWR")
        .otherwise(None),
    ).withColumn(
        "dropoff_airport",
        when(_airport_condition("dropoff_latitude", "dropoff_longitude", jfk), "JFK")
        .when(_airport_condition("dropoff_latitude", "dropoff_longitude", lga), "LGA")
        .when(_airport_condition("dropoff_latitude", "dropoff_longitude", ewr), "EWR")
        .otherwise(None),
    )

    return df


def create_airport_analysis(df: DataFrame, output_path: Path) -> None:
    """
    Airport-specific trip patterns.
    """
    df_air = _with_airport_flags(df)

    airport_trips = df_air.filter(
        col("pickup_airport").isNotNull() | col("dropoff_airport").isNotNull()
    ).withColumn(
        "airport_name",
        when(col("pickup_airport").isNotNull(), col("pickup_airport")).otherwise(
            col("dropoff_airport")
        ),
    ).withColumn(
        "direction",
        when(col("pickup_airport").isNotNull(), "from_airport").otherwise("to_airport"),
    )

    agg_df = airport_trips.groupBy(
        "airport_name",
        "direction",
        "pickup_year",
        "pickup_month",
        "pickup_day_of_week",
        "pickup_hour",
    ).agg(
        count("*").alias("trip_count"),
        avg("fare_amount").alias("avg_fare"),
        avg("trip_distance").alias("avg_distance"),
        avg("trip_duration_minutes").alias("avg_duration"),
    )

    _ensure_output_dir(output_path)
    agg_df.write.mode("overwrite").parquet(str(output_path))


def create_summary_stats(df: DataFrame, output_path: Path) -> None:
    """
    Pre-computed summary statistics for fast API responses.
    
    Single-row table with overall dataset statistics.
    """
    from pyspark.sql.functions import to_timestamp
    
    # Compute summary statistics in one pass
    summary_df = df.agg(
        count("*").alias("total_records"),
        spark_min("tpep_pickup_datetime").alias("min_date"),
        spark_max("tpep_pickup_datetime").alias("max_date"),
        avg("fare_amount").alias("avg_fare"),
        spark_min("fare_amount").alias("min_fare"),
        spark_max("fare_amount").alias("max_fare"),
        stddev("fare_amount").alias("stddev_fare"),
        spark_sum("fare_amount").alias("total_revenue"),
        avg("trip_distance").alias("avg_distance"),
        spark_min("trip_distance").alias("min_distance"),
        spark_max("trip_distance").alias("max_distance"),
        stddev("trip_distance").alias("stddev_distance"),
        avg("trip_duration_minutes").alias("avg_duration"),
        spark_min("trip_duration_minutes").alias("min_duration"),
        spark_max("trip_duration_minutes").alias("max_duration"),
        stddev("trip_duration_minutes").alias("stddev_duration"),
        avg("tip_amount").alias("avg_tip"),
        spark_min("tip_amount").alias("min_tip"),
        spark_max("tip_amount").alias("max_tip"),
        avg("passenger_count").alias("avg_passengers"),
        spark_min("passenger_count").alias("min_passengers"),
        spark_max("passenger_count").alias("max_passengers"),
    )
    
    # Add calculated metrics: fare per mile and tip rate
    summary_df = summary_df.withColumn(
        "avg_fare_per_mile",
        when(col("avg_distance") > 0, col("avg_fare") / col("avg_distance")).otherwise(None)
    ).withColumn(
        "avg_tip_rate",
        when(col("avg_fare") > 0, (col("avg_tip") / col("avg_fare")) * 100).otherwise(None)
    )
    
    _ensure_output_dir(output_path)
    summary_df.write.mode("overwrite").parquet(str(output_path))


def main() -> None:
    """
    Entry point: create all aggregate tables from cleaned data.
    """
    spark = create_spark_session("Create_Aggregate_Tables")
    try:
        cleaned_path = PROCESSED_DATA_DIR / "cleaned_data.parquet"
        print(f"Reading cleaned data from {cleaned_path} ...")
        df = spark.read.parquet(str(cleaned_path))

        print(f"Total rows in cleaned data: {df.count():,}")

        print("Creating aggregate tables...")

        create_temporal_hourly_stats(
            df,
            AGGREGATES_DIR / "temporal_hourly_stats.parquet",
        )
        print("✓ temporal_hourly_stats complete")

        create_geospatial_zone_stats(
            df,
            AGGREGATES_DIR / "geospatial_zone_stats.parquet",
        )
        print("✓ geospatial_zone_stats complete")

        create_route_pairs_top(
            df,
            AGGREGATES_DIR / "route_pairs_top.parquet",
        )
        print("✓ route_pairs_top complete")

        create_economic_fare_analysis(
            df,
            AGGREGATES_DIR / "economic_fare_analysis.parquet",
        )
        print("✓ economic_fare_analysis complete")

        create_tip_behavior_analysis(
            df,
            AGGREGATES_DIR / "tip_behavior_analysis.parquet",
        )
        print("✓ tip_behavior_analysis complete")

        create_airport_analysis(
            df,
            AGGREGATES_DIR / "airport_analysis.parquet",
        )
        print("✓ airport_analysis complete")

        create_summary_stats(
            df,
            AGGREGATES_DIR / "summary_stats.parquet",
        )
        print("✓ summary_stats complete")

        print("\n✅ All aggregate tables created successfully!")
    finally:
        stop_spark_session(spark)


if __name__ == "__main__":
    main()


