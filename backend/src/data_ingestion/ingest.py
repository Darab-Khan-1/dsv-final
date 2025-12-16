"""
Stage 1: Data Ingestion
Convert CSV files to optimized Parquet format
"""

from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import year, month
import logging

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.data_ingestion.schema import get_taxi_schema

logger = logging.getLogger(__name__)


def ingest_csv_to_parquet(
    spark: SparkSession,
    csv_path: Path,
    output_path: Path = None,
    partition_by: list = ["year", "month"]
) -> Path:
    """
    Convert CSV file to Parquet format with partitioning
    
    Args:
        spark: Spark session
        csv_path: Path to CSV file
        output_path: Output Parquet path (optional)
        partition_by: Columns to partition by
        
    Returns:
        Path: Path to output Parquet file/directory
    """
    logger.info(f"Starting ingestion: {csv_path}")
    
    # Define schema
    schema = get_taxi_schema()
    
    # Read CSV with explicit schema
    logger.info("Reading CSV file...")
    df = spark.read \
        .schema(schema) \
        .option("header", "true") \
        .option("nullValue", "") \
        .option("emptyValue", "") \
        .csv(str(csv_path))
    
    # Extract year and month for partitioning
    from pyspark.sql.functions import year, month
    df = df \
        .withColumn("year", year("tpep_pickup_datetime")) \
        .withColumn("month", month("tpep_pickup_datetime"))
    
    # Determine output path
    if output_path is None:
        output_path = PROCESSED_DATA_DIR / "raw_ingested"
    
    # Write as Parquet with partitioning
    logger.info(f"Writing Parquet to: {output_path}")
    df.write \
        .mode("overwrite") \
        .partitionBy(partition_by) \
        .parquet(str(output_path))
    
    # Log statistics
    total_count = df.count()
    logger.info(f"Ingestion complete. Total records: {total_count:,}")
    
    return output_path


def ingest_all_csv_files(
    spark: SparkSession,
    input_dir: Path = None,
    output_dir: Path = None
) -> Path:
    """
    Ingest all CSV files from input directory
    
    Args:
        spark: Spark session
        input_dir: Directory containing CSV files
        output_dir: Output directory for Parquet files
        
    Returns:
        Path: Path to output directory
    """
    if input_dir is None:
        input_dir = RAW_DATA_DIR
    
    if output_dir is None:
        output_dir = PROCESSED_DATA_DIR / "raw_ingested"
    
    # Find all CSV files
    csv_files = list(input_dir.glob("*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {input_dir}")
    
    logger.info(f"Found {len(csv_files)} CSV file(s)")
    
    # Read all CSV files and combine
    schema = get_taxi_schema()
    dfs = []
    
    for csv_file in csv_files:
        logger.info(f"Reading {csv_file.name}...")
        df = spark.read \
            .schema(schema) \
            .option("header", "true") \
            .option("nullValue", "") \
            .option("emptyValue", "") \
            .csv(str(csv_file))
        
        # Add year and month columns
        from pyspark.sql.functions import year, month
        df = df \
            .withColumn("year", year("tpep_pickup_datetime")) \
            .withColumn("month", month("tpep_pickup_datetime"))
        
        dfs.append(df)
    
    # Union all DataFrames (process in batches to reduce memory)
    logger.info("Combining all DataFrames...")
    from functools import reduce
    combined_df = reduce(lambda df1, df2: df1.union(df2), dfs)
    
    # Coalesce to reduce partitions before write (coalesce doesn't shuffle, saves memory)
    logger.info("Coalescing data to reduce partitions for write operation...")
    num_partitions = combined_df.rdd.getNumPartitions()
    target_partitions = min(100, num_partitions)  # Cap at 100 partitions
    combined_df = combined_df.coalesce(target_partitions)
    
    # Write combined data as Parquet (partitioned for efficient reads, memory-optimized)
    logger.info(f"Writing combined Parquet to: {output_dir}")
    combined_df.write \
        .mode("overwrite") \
        .partitionBy("year", "month") \
        .option("maxRecordsPerFile", 500000) \
        .option("compression", "snappy") \
        .parquet(str(output_dir))
    
    # Log final statistics
    total_count = combined_df.count()
    logger.info(f"Ingestion complete. Total records: {total_count:,}")
    
    # Show year/month distribution
    year_month_dist = combined_df \
        .groupBy("year", "month") \
        .count() \
        .orderBy("year", "month") \
        .collect()
    
    logger.info("Year/Month distribution:")
    for row in year_month_dist:
        year = row['year']
        month = row['month']
        count = row['count']
        logger.info(f"  {year}-{month:02d}: {count:,} records")
    
    return output_dir


if __name__ == "__main__":
    # Example usage
    from src.utils.spark_utils import create_spark_session, stop_spark_session
    
    logging.basicConfig(level=logging.INFO)
    
    spark = create_spark_session("Data_Ingestion")
    
    try:
        # Ingest all CSV files
        output_path = ingest_all_csv_files(spark)
        print(f"✅ Data ingested successfully to: {output_path}")
    finally:
        stop_spark_session(spark)

