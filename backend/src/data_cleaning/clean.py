"""
Stage 2: Data Cleaning
Handle missing values, invalid data, and calculate derived features
"""

from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    when,
    isnan,
    isnull,
    unix_timestamp,
    round as spark_round,
    hour,
    dayofweek,
    month,
    year,
)
from pyspark.sql.types import DoubleType
import logging

from src.config import PROCESSED_DATA_DIR, CLEANING_THRESHOLDS

logger = logging.getLogger(__name__)


def calculate_trip_duration(df):
    """
    Calculate trip duration in minutes
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with trip_duration_minutes column
    """
    logger.info("Calculating trip duration...")
    
    df = df.withColumn(
        "trip_duration_minutes",
        (unix_timestamp("tpep_dropoff_datetime") - 
         unix_timestamp("tpep_pickup_datetime")) / 60.0
    )
    
    return df


def clean_data(
    spark: SparkSession, input_path: Path, output_path: Path = None
) -> Path:
    """
    Clean NYC taxi data
    
    Args:
        spark: Spark session
        input_path: Path to input Parquet data
        output_path: Path to output cleaned data
        
    Returns:
        Path: Path to cleaned data
    """
    logger.info("Starting data cleaning...")
    
    # Read data
    logger.info(f"Reading data from: {input_path}")
    df = spark.read.parquet(str(input_path))
    
    initial_count = df.count()
    logger.info(f"Initial record count: {initial_count:,}")
    
    # Calculate trip duration
    df = calculate_trip_duration(df)
    
    # Apply cleaning filters
    logger.info("Applying cleaning filters...")
    
    # Filter by trip duration
    df = df.filter(
        (col("trip_duration_minutes") > CLEANING_THRESHOLDS["trip_duration_min"]) &
        (col("trip_duration_minutes") < CLEANING_THRESHOLDS["trip_duration_max"])
    )
    
    # Filter by trip distance
    df = df.filter(
        (col("trip_distance") > CLEANING_THRESHOLDS["trip_distance_min"]) &
        (col("trip_distance") < CLEANING_THRESHOLDS["trip_distance_max"])
    )
    
    # Filter by fare amount
    df = df.filter(
        (col("fare_amount") > CLEANING_THRESHOLDS["fare_amount_min"]) &
        (col("fare_amount") < CLEANING_THRESHOLDS["fare_amount_max"])
    )
    
    # Filter by passenger count
    df = df.filter(
        (col("passenger_count") >= CLEANING_THRESHOLDS["passenger_count_min"]) &
        (col("passenger_count") <= CLEANING_THRESHOLDS["passenger_count_max"])
    )
    
    # Filter by NYC coordinates
    df = df.filter(
        (col("pickup_latitude") >= CLEANING_THRESHOLDS["nyc_lat_min"]) &
        (col("pickup_latitude") <= CLEANING_THRESHOLDS["nyc_lat_max"]) &
        (col("pickup_longitude") >= CLEANING_THRESHOLDS["nyc_lon_min"]) &
        (col("pickup_longitude") <= CLEANING_THRESHOLDS["nyc_lon_max"]) &
        (col("dropoff_latitude") >= CLEANING_THRESHOLDS["nyc_lat_min"]) &
        (col("dropoff_latitude") <= CLEANING_THRESHOLDS["nyc_lat_max"]) &
        (col("dropoff_longitude") >= CLEANING_THRESHOLDS["nyc_lon_min"]) &
        (col("dropoff_longitude") <= CLEANING_THRESHOLDS["nyc_lon_max"])
    )
    
    # Handle null values in critical columns
    logger.info("Handling null values...")
    df = df.dropna(subset=[
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "fare_amount",
        "trip_distance"
    ])
    
    # Fill null passenger_count with 1 (default)
    df = df.fillna({"passenger_count": 1})
    
    # Fill null tip_amount with 0
    df = df.fillna({"tip_amount": 0.0})
    
    # Add geospatial grid columns for hotspot analysis
    logger.info("Adding geospatial grid columns...")
    df = (
        df.withColumn("pickup_lat_grid", spark_round(col("pickup_latitude"), 2))
        .withColumn("pickup_lon_grid", spark_round(col("pickup_longitude"), 2))
        .withColumn("dropoff_lat_grid", spark_round(col("dropoff_latitude"), 2))
        .withColumn("dropoff_lon_grid", spark_round(col("dropoff_longitude"), 2))
    )

    # Add temporal features (and explicit partition columns)
    logger.info("Adding temporal and partition columns...")
    df = (
        df.withColumn("pickup_hour", hour("tpep_pickup_datetime"))
        .withColumn("pickup_day_of_week", dayofweek("tpep_pickup_datetime"))
        .withColumn("pickup_month", month("tpep_pickup_datetime"))
        .withColumn("pickup_year", year("tpep_pickup_datetime"))
        # Explicit partition columns used for partition pruning
        .withColumn("year", year("tpep_pickup_datetime").cast("int"))
        .withColumn("month", month("tpep_pickup_datetime").cast("int"))
    )
    
    # Final count (before repartitioning to avoid memory issues)
    final_count = df.count()
    dropped = initial_count - final_count
    drop_percentage = (dropped / initial_count) * 100
    
    logger.info(f"Cleaning complete!")
    logger.info(f"  Initial records: {initial_count:,}")
    logger.info(f"  Final records: {final_count:,}")
    logger.info(f"  Dropped: {dropped:,} ({drop_percentage:.2f}%)")
    
    # Determine output path
    if output_path is None:
        output_path = PROCESSED_DATA_DIR / "cleaned_data.parquet"

    # Repartition by time only (no expensive sort) for safer memory usage
    logger.info("Repartitioning by year/month for partitioned write (no in-memory sort)...")
    df = df.repartition("year", "month")

    # Write cleaned data (partitioned for efficient reads, with conservative settings)
    logger.info(f"Writing cleaned data to: {output_path}")
    (
        df.write.mode("overwrite")
        .partitionBy("year", "month")
        .option("maxRecordsPerFile", 500000)
        .option("compression", "snappy")
        .parquet(str(output_path))
    )
    
    # Show schema
    logger.info("Cleaned data schema:")
    df.printSchema()
    
    return output_path


def validate_data_quality(df):
    """
    Validate data quality after cleaning
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        dict: Quality metrics
    """
    from pyspark.sql.functions import col, isnan, isnull
    
    quality_metrics = {}
    
    # Check for nulls in critical columns
    critical_cols = ["tpep_pickup_datetime", "fare_amount", "trip_distance"]
    for col_name in critical_cols:
        null_count = df.filter(col(col_name).isNull()).count()
        quality_metrics[f"{col_name}_nulls"] = null_count
    
    # Check data ranges
    quality_metrics["min_fare"] = df.agg({"fare_amount": "min"}).collect()[0][0]
    quality_metrics["max_fare"] = df.agg({"fare_amount": "max"}).collect()[0][0]
    quality_metrics["min_distance"] = df.agg({"trip_distance": "min"}).collect()[0][0]
    quality_metrics["max_distance"] = df.agg({"trip_distance": "max"}).collect()[0][0]
    
    return quality_metrics


if __name__ == "__main__":
    # Example usage
    from src.utils.spark_utils import create_spark_session, stop_spark_session
    
    logging.basicConfig(level=logging.INFO)
    
    spark = create_spark_session("Data_Cleaning")
    
    try:
        # Clean ingested data
        input_path = PROCESSED_DATA_DIR / "raw_ingested"
        output_path = clean_data(spark, input_path)
        print(f"✅ Data cleaned successfully. Output: {output_path}")
        
        # Validate quality
        df = spark.read.parquet(str(output_path))
        quality = validate_data_quality(df)
        print("Data quality metrics:", quality)
    finally:
        stop_spark_session(spark)

