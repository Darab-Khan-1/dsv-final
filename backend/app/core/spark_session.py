"""
Spark Session Management
Singleton pattern for Spark session
"""

import logging

logger = logging.getLogger(__name__)

_spark_session = None


def _import_spark():
    """Lazy import of PySpark to avoid errors if not installed"""
    try:
        from pyspark.sql import SparkSession
        return SparkSession
    except ImportError:
        raise ImportError(
            "PySpark is not installed. Install it with: pip install pyspark"
        )


def get_spark_session():
    """
    Get or create Spark session (singleton)
    
    Returns:
        SparkSession: Spark session instance
    """
    global _spark_session
    
    if _spark_session is None:
        SparkSession = _import_spark()
        from app.core.config import settings
        
        logger.info("Creating new Spark session...")
        _spark_session = SparkSession.builder \
            .appName(settings.SPARK_APP_NAME) \
            .master(settings.SPARK_MASTER) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
            .config("spark.sql.parquet.compression.codec", "snappy") \
            .config("spark.sql.shuffle.partitions", "200") \
            .getOrCreate()
        
        logger.info(f"Spark session created: {_spark_session.version}")
    
    return _spark_session


def stop_spark_session():
    """Stop Spark session"""
    global _spark_session
    
    if _spark_session is not None:
        logger.info("Stopping Spark session...")
        _spark_session.stop()
        _spark_session = None
        logger.info("Spark session stopped")


def get_dataframe_from_parquet(path: str):
    """
    Load DataFrame from Parquet file
    
    Args:
        path: Path to Parquet file
        
    Returns:
        DataFrame: Spark DataFrame
    """
    spark = get_spark_session()
    return spark.read.parquet(path)

