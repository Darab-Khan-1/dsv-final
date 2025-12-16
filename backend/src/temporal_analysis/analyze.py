"""
Stage 3.1: Temporal Analysis
Analyze temporal patterns in taxi trips
"""

from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    hour,
    dayofweek,
    count,
    avg,
    min,
    max,
    stddev,
    percentile_approx,
    desc,
)
import logging

from src.config import PROCESSED_DATA_DIR, OUTPUT_DATA_DIR

logger = logging.getLogger(__name__)


class TemporalAnalysis:
    """Temporal analysis operations"""
    
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
    
    def trips_by_hour(self, year=None, month=None, day_of_week=None):
        """Get trip counts by hour"""
        logger.info("Analyzing trips by hour...")
        
        df = self.df
        if year is not None:
            df = df.filter(col("year") == int(year))
        if month is not None:
            df = df.filter(col("month") == int(month))
        if day_of_week is not None:
            df = df.filter(col("pickup_day_of_week") == int(day_of_week))
        
        result = df \
            .groupBy("pickup_hour") \
            .agg(count("*").alias("trip_count")) \
            .orderBy("pickup_hour") \
            .collect()
        
        return [{"hour": row.pickup_hour, "trip_count": row.trip_count} for row in result]
    
    def trips_by_day(self, year=None, month=None):
        """Get trip counts by day of week"""
        logger.info("Analyzing trips by day of week...")
        
        df = self.df
        if year is not None:
            df = df.filter(col("year") == int(year))
        if month is not None:
            df = df.filter(col("month") == int(month))
        
        result = df \
            .groupBy("pickup_day_of_week") \
            .agg(count("*").alias("trip_count")) \
            .orderBy("pickup_day_of_week") \
            .collect()
        
        return [{"day_of_week": row.pickup_day_of_week, "trip_count": row.trip_count} for row in result]
    
    def trips_by_month(self, year=None):
        """Get trip counts by month"""
        logger.info("Analyzing trips by month...")
        
        df = self.df
        if year is not None:
            df = df.filter(col("year") == int(year))
        
        result = df.groupBy("year", "month") \
            .agg(count("*").alias("trip_count")) \
            .orderBy("year", "month") \
            .collect()
        
        return [{"year": row.year, "month": row.month, "trip_count": row.trip_count} for row in result]
    
    def peak_hours(self, top_n=10):
        """Get peak pickup hours"""
        logger.info(f"Identifying top {top_n} peak hours...")
        
        result = self.df \
            .withColumn("hour", hour("tpep_pickup_datetime")) \
            .groupBy("hour") \
            .agg(count("*").alias("trip_count")) \
            .orderBy(desc("trip_count")) \
            .limit(top_n) \
            .collect()
        
        return [{"hour": row.hour, "trip_count": row.trip_count} for row in result]
    
    def duration_distribution(self, year=None, month=None):
        """Get trip duration distribution statistics"""
        logger.info("Calculating duration distribution...")
        
        df = self.df
        if year is not None:
            df = df.filter(col("year") == int(year))
        if month is not None:
            df = df.filter(col("month") == int(month))
        
        stats = df.agg(
            avg("trip_duration_minutes").alias("mean"),
            stddev("trip_duration_minutes").alias("stddev"),
            min("trip_duration_minutes").alias("min"),
            max("trip_duration_minutes").alias("max"),
            percentile_approx("trip_duration_minutes", 0.5).alias("median"),
            percentile_approx("trip_duration_minutes", 0.25).alias("p25"),
            percentile_approx("trip_duration_minutes", 0.75).alias("p75"),
            percentile_approx("trip_duration_minutes", 0.95).alias("p95")
        ).collect()[0]
        
        return {
            "mean": stats.mean,
            "stddev": stats.stddev,
            "min": stats.min,
            "max": stats.max,
            "median": stats.median,
            "p25": stats.p25,
            "p75": stats.p75,
            "p95": stats.p95
        }
    
    def fare_trends(self, group_by="month", year=None):
        """Get fare trends over time"""
        logger.info(f"Analyzing fare trends grouped by {group_by}...")
        
        df = self.df
        if year is not None:
            df = df.filter(col("year") == int(year))
        
        if group_by == "hour":
            result = df \
                .withColumn("hour", hour("tpep_pickup_datetime")) \
                .groupBy("hour") \
                .agg(
                    avg("fare_amount").alias("avg_fare"),
                    avg("trip_distance").alias("avg_distance")
                ) \
                .orderBy("hour") \
                .collect()
            return [{"hour": row.hour, "avg_fare": row.avg_fare, "avg_distance": row.avg_distance} for row in result]
        
        elif group_by == "day":
            result = df \
                .withColumn("day_of_week", dayofweek("tpep_pickup_datetime")) \
                .groupBy("day_of_week") \
                .agg(
                    avg("fare_amount").alias("avg_fare"),
                    avg("trip_distance").alias("avg_distance")
                ) \
                .orderBy("day_of_week") \
                .collect()
            return [{"day_of_week": row.day_of_week, "avg_fare": row.avg_fare, "avg_distance": row.avg_distance} for row in result]
        
        else:  # month
            result = df.groupBy("year", "month") \
                .agg(
                    avg("fare_amount").alias("avg_fare"),
                    avg("trip_distance").alias("avg_distance")
                ) \
                .orderBy("year", "month") \
                .collect()
            return [{"year": row.year, "month": row.month, "avg_fare": row.avg_fare, "avg_distance": row.avg_distance} for row in result]
    
    def save_results(self, results: dict, output_file: str = "temporal_analysis_results.json"):
        """Save analysis results"""
        import json
        
        output_path = OUTPUT_DATA_DIR / output_file
        logger.info(f"Saving results to: {output_path}")
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return output_path


def run_temporal_analysis(spark: SparkSession, df=None):
    """Run complete temporal analysis"""
    logger.info("=" * 60)
    logger.info("TEMPORAL ANALYSIS")
    logger.info("=" * 60)
    
    analyzer = TemporalAnalysis(spark)
    if df is None:
        analyzer.load_data()
    else:
        analyzer.df = df
    
    results = {}
    
    # Trips by hour
    results["trips_by_hour"] = analyzer.trips_by_hour()
    logger.info(f"✅ Trips by hour: {len(results['trips_by_hour'])} hours")
    
    # Trips by day
    results["trips_by_day"] = analyzer.trips_by_day()
    logger.info(f"✅ Trips by day: {len(results['trips_by_day'])} days")
    
    # Trips by month
    results["trips_by_month"] = analyzer.trips_by_month()
    logger.info(f"✅ Trips by month: {len(results['trips_by_month'])} months")
    
    # Peak hours
    results["peak_hours"] = analyzer.peak_hours(top_n=10)
    logger.info(f"✅ Peak hours identified: {len(results['peak_hours'])} hours")
    
    # Duration distribution
    results["duration_distribution"] = analyzer.duration_distribution()
    logger.info("✅ Duration distribution calculated")
    
    # Fare trends
    results["fare_trends_by_hour"] = analyzer.fare_trends(group_by="hour")
    results["fare_trends_by_month"] = analyzer.fare_trends(group_by="month")
    logger.info("✅ Fare trends calculated")
    
    # Save results
    output_path = analyzer.save_results(results)
    logger.info(f"✅ Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    from src.utils.spark_utils import create_spark_session, stop_spark_session
    
    logging.basicConfig(level=logging.INFO)
    
    spark = create_spark_session("Temporal_Analysis")
    
    try:
        results = run_temporal_analysis(spark)
        print("✅ Temporal analysis complete!")
    finally:
        stop_spark_session(spark)

