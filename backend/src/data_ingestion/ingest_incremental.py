"""
Phase 5: Incremental Ingestion and Aggregate Updates

This module ingests a new monthly CSV file, applies the existing cleaning
logic, appends it as a new partition to the cleaned parquet dataset, and
updates the aggregate tables incrementally.
"""

from pathlib import Path
from typing import Tuple

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count, avg, expr, sum as spark_sum

from src.config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from src.data_ingestion.schema import get_taxi_schema
from src.utils.spark_utils import create_spark_session, stop_spark_session
from src.data_cleaning.clean import clean_data
from src.aggregation.create_aggregate_tables import (
    create_temporal_hourly_stats,
    create_geospatial_zone_stats,
    create_route_pairs_top,
    create_economic_fare_analysis,
    create_tip_behavior_analysis,
    create_airport_analysis,
    AGGREGATES_DIR,
)


def ingest_new_data(new_csv_path: Path, cleaned_parquet_path: Path) -> Tuple[int, int]:
    """
    Ingest new monthly data and append to existing cleaned parquet.
    """
    spark = create_spark_session("Ingest_Incremental")
    try:
        schema = get_taxi_schema()
        print(f"Reading new data from {new_csv_path} ...")
        new_df = (
            spark.read.schema(schema)
            .option("header", "true")
            .option("nullValue", "")
            .option("emptyValue", "")
            .csv(str(new_csv_path))
        )

        # Write to temp parquet, then reuse existing cleaning pipeline
        tmp_raw = PROCESSED_DATA_DIR / "raw_ingested_incremental"
        new_df.write.mode("overwrite").parquet(str(tmp_raw))

        # Clean using existing cleaning function (which also partitions by year/month)
        cleaned_path = clean_data(spark, tmp_raw, output_path=cleaned_parquet_path)

        # Extract year/month from cleaned data
        cleaned_df = spark.read.parquet(str(cleaned_parquet_path))
        year_val = cleaned_df.select("year").orderBy("year").first()[0]
        month_val = cleaned_df.select("month").orderBy("month").first()[0]

        print(f"✓ Incremental data cleaned and appended for {year_val}-{month_val:02d}")
        return int(year_val), int(month_val)
    finally:
        stop_spark_session(spark)


def _append_temporal_incremental(df_new: DataFrame) -> None:
    spark = df_new.sparkSession
    existing_path = AGGREGATES_DIR / "temporal_hourly_stats.parquet"
    existing = spark.read.parquet(str(existing_path))

    new_agg = (
        df_new.groupBy(
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
    )

    updated = existing.unionByName(new_agg)
    updated.write.mode("overwrite").parquet(str(existing_path))


def update_aggregates_incremental(year: int, month: int) -> None:
    """
    Update aggregate tables with new partition data only.
    """
    spark = create_spark_session("Update_Aggregates_Incremental")
    try:
        cleaned_path = PROCESSED_DATA_DIR / "cleaned_data.parquet"
        print(f"Reading new partition {year}-{month:02d} from {cleaned_path} ...")
        new_partition = (
            spark.read.parquet(str(cleaned_path))
            .filter((col("year") == int(year)) & (col("month") == int(month)))
        )

        print(f"New partition size: {new_partition.count():,} rows")

        # Temporal
        print("Updating temporal_hourly_stats ...")
        _append_temporal_incremental(new_partition)

        # For other aggregates, recompute from new partition and union
        print("Updating geospatial_zone_stats ...")
        geospatial_path = AGGREGATES_DIR / "geospatial_zone_stats.parquet"
        existing_geo = spark.read.parquet(str(geospatial_path))
        new_geo = create_geospatial_zone_stats(
            new_partition, geospatial_path.with_name("_tmp_geo.parquet")
        )
        # create_geospatial_zone_stats writes, so re-read tmp
        new_geo_df = spark.read.parquet(
            str(geospatial_path.with_name("_tmp_geo.parquet"))
        )
        updated_geo = existing_geo.unionByName(new_geo_df)
        updated_geo.write.mode("overwrite").parquet(str(geospatial_path))

        print("Updating route_pairs_top ...")
        route_path = AGGREGATES_DIR / "route_pairs_top.parquet"
        existing_route = spark.read.parquet(str(route_path))
        create_route_pairs_top(
            new_partition, route_path.with_name("_tmp_route.parquet")
        )
        new_route_df = spark.read.parquet(
            str(route_path.with_name("_tmp_route.parquet"))
        )
        updated_route = existing_route.unionByName(new_route_df)
        updated_route.write.mode("overwrite").parquet(str(route_path))

        print("Updating economic_fare_analysis ...")
        econ_path = AGGREGATES_DIR / "economic_fare_analysis.parquet"
        existing_econ = spark.read.parquet(str(econ_path))
        create_economic_fare_analysis(
            new_partition, econ_path.with_name("_tmp_econ.parquet")
        )
        new_econ_df = spark.read.parquet(
            str(econ_path.with_name("_tmp_econ.parquet"))
        )
        updated_econ = existing_econ.unionByName(new_econ_df)
        updated_econ.write.mode("overwrite").parquet(str(econ_path))

        print("Updating tip_behavior_analysis ...")
        tip_path = AGGREGATES_DIR / "tip_behavior_analysis.parquet"
        existing_tip = spark.read.parquet(str(tip_path))
        create_tip_behavior_analysis(
            new_partition, tip_path.with_name("_tmp_tip.parquet")
        )
        new_tip_df = spark.read.parquet(str(tip_path.with_name("_tmp_tip.parquet")))
        updated_tip = existing_tip.unionByName(new_tip_df)
        updated_tip.write.mode("overwrite").parquet(str(tip_path))

        print("Updating airport_analysis ...")
        airport_path = AGGREGATES_DIR / "airport_analysis.parquet"
        existing_airport = spark.read.parquet(str(airport_path))
        create_airport_analysis(
            new_partition, airport_path.with_name("_tmp_airport.parquet")
        )
        new_airport_df = spark.read.parquet(
            str(airport_path.with_name("_tmp_airport.parquet"))
        )
        updated_airport = existing_airport.unionByName(new_airport_df)
        updated_airport.write.mode("overwrite").parquet(str(airport_path))

        print("✅ All aggregates updated successfully.")
    finally:
        stop_spark_session(spark)


def main(new_csv: str) -> None:
    csv_path = (RAW_DATA_DIR / new_csv) if not new_csv.startswith("/") else Path(new_csv)
    cleaned_path = PROCESSED_DATA_DIR / "cleaned_data.parquet"

    year, month = ingest_new_data(csv_path, cleaned_path)
    update_aggregates_incremental(year, month)
    print("\n✅ Incremental processing complete.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m src.data_ingestion.ingest_incremental <path_or_filename_to_new_csv>")
        sys.exit(1)

    main(sys.argv[1])


