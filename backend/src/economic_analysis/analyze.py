"""
Stage 3.3: Economic Analysis
Analyze economic patterns in taxi trips
"""

from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, avg, hour, when,
    percentile_approx
)
from pyspark.ml.stat import Correlation
from pyspark.ml.feature import VectorAssembler
import logging

from src.config import PROCESSED_DATA_DIR, OUTPUT_DATA_DIR

logger = logging.getLogger(__name__)


class EconomicAnalysis:
    """Economic analysis operations"""
    
    def __init__(self, spark: SparkSession, data_path: Path = None):
        self.spark = spark
        if data_path is None:
            data_path = PROCESSED_DATA_DIR / "cleaned_data.parquet"
        self.data_path = data_path
        self.df = None
    
    def load_data(self):
        """Load cleaned data"""
        logger.info(f"Loading data from: {self.data_path}")
        self.df = self.spark.read.parquet(str(self.data_path))
        logger.info(f"Data loaded. Records: {self.df.count():,}")
        return self.df
    
    def correlations(self):
        """Calculate correlation matrix"""
        logger.info("Calculating correlations...")
        
        # Prepare numeric columns
        numeric_cols = ["fare_amount", "trip_distance", "trip_duration_minutes"]
        assembler = VectorAssembler(inputCols=numeric_cols, outputCol="features")
        df_vector = assembler.transform(self.df).select("features")
        
        # Calculate correlation
        correlation_matrix = Correlation.corr(df_vector, "features").head()[0]
        corr_array = correlation_matrix.toArray()
        
        return {
            "columns": numeric_cols,
            "correlation_matrix": corr_array.tolist()
        }
    
    def tip_analysis(self, group_by="payment_type"):
        """Analyze tip behavior"""
        logger.info(f"Analyzing tip behavior by {group_by}...")
        
        df_tip = self.df.withColumn(
            "tip_percentage",
            (col("tip_amount") / col("fare_amount")) * 100
        )
        
        if group_by == "payment_type":
            result = df_tip \
                .groupBy("payment_type") \
                .agg(
                    avg("tip_percentage").alias("avg_tip_percent"),
                    count("*").alias("trip_count")
                ) \
                .collect()
            return [
                {
                    "payment_type": row.payment_type,
                    "avg_tip_percent": row.avg_tip_percent,
                    "trip_count": row.trip_count
                }
                for row in result
            ]
        
        elif group_by == "hour":
            result = df_tip \
                .withColumn("hour", hour("tpep_pickup_datetime")) \
                .groupBy("hour") \
                .agg(
                    avg("tip_percentage").alias("avg_tip_percent"),
                    count("*").alias("trip_count")
                ) \
                .orderBy("hour") \
                .collect()
            return [
                {
                    "hour": row.hour,
                    "avg_tip_percent": row.avg_tip_percent,
                    "trip_count": row.trip_count
                }
                for row in result
            ]
        
        elif group_by == "distance_bucket":
            df_bucketed = df_tip.withColumn(
                "distance_bucket",
                when(col("trip_distance") < 2, "Short (<2 mi)")
                .when(col("trip_distance") < 5, "Medium (2-5 mi)")
                .otherwise("Long (>5 mi)")
            )
            
            result = df_bucketed \
                .groupBy("distance_bucket") \
                .agg(
                    avg("tip_percentage").alias("avg_tip_percent"),
                    count("*").alias("trip_count")
                ) \
                .collect()
            return [
                {
                    "distance_bucket": row.distance_bucket,
                    "avg_tip_percent": row.avg_tip_percent,
                    "trip_count": row.trip_count
                }
                for row in result
            ]
        
        else:
            return []
    
    def revenue_analysis(self, group_by="hour"):
        """Analyze revenue patterns"""
        logger.info(f"Analyzing revenue by {group_by}...")
        
        if group_by == "hour":
            result = self.df \
                .groupBy("pickup_hour") \
                .agg(
                    avg("total_amount").alias("avg_revenue"),
                    count("*").alias("trip_count")
                ) \
                .orderBy("pickup_hour") \
                .collect()
            return [
                {
                    "hour": row.pickup_hour,
                    "avg_revenue": row.avg_revenue,
                    "trip_count": row.trip_count
                }
                for row in result
            ]
        else:
            return []
    
    def market_share(self):
        """Analyze vendor market share"""
        logger.info("Analyzing vendor market share...")
        
        result = self.df \
            .groupBy("VendorID") \
            .agg(
                count("*").alias("trip_count"),
                avg("total_amount").alias("avg_fare")
            ) \
            .collect()
        
        total_trips = sum(row.trip_count for row in result)
        
        return [
            {
                "vendor_id": row.VendorID,
                "trip_count": row.trip_count,
                "market_share_percent": (row.trip_count / total_trips) * 100,
                "avg_fare": row.avg_fare
            }
            for row in result
        ]
    
    def save_results(self, results: dict, output_file: str = "economic_analysis_results.json"):
        """Save analysis results"""
        import json
        
        output_path = OUTPUT_DATA_DIR / output_file
        logger.info(f"Saving results to: {output_path}")
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return output_path


def run_economic_analysis(spark: SparkSession, df=None):
    """Run complete economic analysis"""
    logger.info("=" * 60)
    logger.info("ECONOMIC ANALYSIS")
    logger.info("=" * 60)
    
    analyzer = EconomicAnalysis(spark)
    if df is None:
        analyzer.load_data()
    else:
        analyzer.df = df
    
    results = {}
    
    # Correlations
    results["correlations"] = analyzer.correlations()
    logger.info("✅ Correlations calculated")
    
    # Tip analysis
    results["tip_by_payment_type"] = analyzer.tip_analysis("payment_type")
    results["tip_by_hour"] = analyzer.tip_analysis("hour")
    results["tip_by_distance"] = analyzer.tip_analysis("distance_bucket")
    logger.info("✅ Tip analysis complete")
    
    # Revenue analysis
    results["revenue_by_hour"] = analyzer.revenue_analysis("hour")
    logger.info("✅ Revenue analysis complete")
    
    # Market share
    results["market_share"] = analyzer.market_share()
    logger.info("✅ Market share analysis complete")
    
    # Save results
    output_path = analyzer.save_results(results)
    logger.info(f"✅ Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    from src.utils.spark_utils import create_spark_session, stop_spark_session
    
    logging.basicConfig(level=logging.INFO)
    
    spark = create_spark_session("Economic_Analysis")
    
    try:
        results = run_economic_analysis(spark)
        print("✅ Economic analysis complete!")
    finally:
        stop_spark_session(spark)

