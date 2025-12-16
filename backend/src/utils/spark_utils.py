"""
Spark Utility Functions
"""

from pathlib import Path
from pyspark.sql import SparkSession
from src.config import SPARK_CONFIG
import logging

logger = logging.getLogger(__name__)


def create_spark_session(app_name: str = "NYC_Taxi_Analysis") -> SparkSession:
    """
    Create and configure Spark session (optimized for limited RAM)
    
    Args:
        app_name: Application name
        
    Returns:
        SparkSession: Configured Spark session
    """
    logger.info(f"Creating Spark session: {app_name} (optimized for limited RAM)")
    
    builder = SparkSession.builder \
        .appName(app_name) \
        .master("local[*]")
    
    # Apply Spark configurations (config() requires key-value pairs, not kwargs)
    for key, value in SPARK_CONFIG.items():
        builder = builder.config(key, value)
    
    spark = builder.getOrCreate()
    
    # Set checkpoint directory for disk-based operations
    checkpoint_dir = Path("/tmp/spark-checkpoints") / app_name
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    spark.sparkContext.setCheckpointDir(str(checkpoint_dir))
    
    # Set log level to reduce memory usage
    spark.sparkContext.setLogLevel("WARN")
    
    logger.info(f"Spark session created. Version: {spark.version}")
    logger.info(f"Memory settings: executor={SPARK_CONFIG.get('spark.executor.memory', 'default')}, driver={SPARK_CONFIG.get('spark.driver.memory', 'default')}")
    logger.info(f"Partitions: shuffle={SPARK_CONFIG.get('spark.sql.shuffle.partitions', 'default')}")
    return spark


def stop_spark_session(spark: SparkSession):
    """Stop Spark session (safely ignore if Java gateway already closed)"""
    from py4j.protocol import Py4JNetworkError
    logger.info("Stopping Spark session...")
    try:
        spark.stop()
        logger.info("Spark session stopped")
    except (ConnectionRefusedError, Py4JNetworkError) as e:
        logger.warning(f"Spark already stopped or Java gateway closed: {e}")

