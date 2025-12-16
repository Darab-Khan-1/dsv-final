"""
Stage 3.2: Geospatial Analysis
Analyze spatial patterns in taxi trips
"""

from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, avg, round as spark_round,
    concat, desc
)
import logging

from src.config import PROCESSED_DATA_DIR, OUTPUT_DATA_DIR, AIRPORT_COORDINATES

logger = logging.getLogger(__name__)


class GeospatialAnalysis:
    """Geospatial analysis operations"""
    
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
    
    def pickup_hotspots(self, top_n=20, min_trips=100):
        """Get top pickup hotspots"""
        logger.info(f"Identifying top {top_n} pickup hotspots...")
        
        result = self.df \
            .groupBy("pickup_lat_grid", "pickup_lon_grid") \
            .agg(count("*").alias("trip_count")) \
            .filter(col("trip_count") >= min_trips) \
            .orderBy(desc("trip_count")) \
            .limit(top_n) \
            .collect()
        
        return [
            {
                "latitude": row.pickup_lat_grid,
                "longitude": row.pickup_lon_grid,
                "trip_count": row.trip_count
            }
            for row in result
        ]
    
    def dropoff_hotspots(self, top_n=20, min_trips=100):
        """Get top dropoff hotspots"""
        logger.info(f"Identifying top {top_n} dropoff hotspots...")
        
        result = self.df \
            .groupBy("dropoff_lat_grid", "dropoff_lon_grid") \
            .agg(count("*").alias("trip_count")) \
            .filter(col("trip_count") >= min_trips) \
            .orderBy(desc("trip_count")) \
            .limit(top_n) \
            .collect()
        
        return [
            {
                "latitude": row.dropoff_lat_grid,
                "longitude": row.dropoff_lon_grid,
                "trip_count": row.trip_count
            }
            for row in result
        ]
    
    def route_pairs(self, top_n=20):
        """Get most common route pairs"""
        logger.info(f"Identifying top {top_n} route pairs...")
        
        result = self.df \
            .withColumn(
                "pickup_grid",
                concat(
                    col("pickup_lat_grid"),
                    col("pickup_lon_grid")
                )
            ) \
            .withColumn(
                "dropoff_grid",
                concat(
                    col("dropoff_lat_grid"),
                    col("dropoff_lon_grid")
                )
            ) \
            .groupBy("pickup_lat_grid", "pickup_lon_grid", 
                     "dropoff_lat_grid", "dropoff_lon_grid") \
            .agg(
                count("*").alias("trip_count"),
                avg("fare_amount").alias("avg_fare"),
                avg("trip_distance").alias("avg_distance")
            ) \
            .orderBy(desc("trip_count")) \
            .limit(top_n) \
            .collect()
        
        return [
            {
                "pickup_lat": row.pickup_lat_grid,
                "pickup_lon": row.pickup_lon_grid,
                "dropoff_lat": row.dropoff_lat_grid,
                "dropoff_lon": row.dropoff_lon_grid,
                "trip_count": row.trip_count,
                "avg_fare": row.avg_fare,
                "avg_distance": row.avg_distance
            }
            for row in result
        ]
    
    def airport_analysis(self):
        """Analyze airport trips"""
        logger.info("Analyzing airport trips...")
        
        # Define airport zones (within 0.05 degrees)
        airport_radius = 0.05
        
        # JFK trips
        jfk_trips = self.df.filter(
            (col("pickup_latitude") >= AIRPORT_COORDINATES["JFK"]["lat"] - airport_radius) &
            (col("pickup_latitude") <= AIRPORT_COORDINATES["JFK"]["lat"] + airport_radius) &
            (col("pickup_longitude") >= AIRPORT_COORDINATES["JFK"]["lon"] - airport_radius) &
            (col("pickup_longitude") <= AIRPORT_COORDINATES["JFK"]["lon"] + airport_radius)
        )
        
        jfk_stats = jfk_trips.agg(
            count("*").alias("trip_count"),
            avg("fare_amount").alias("avg_fare"),
            avg("trip_distance").alias("avg_distance"),
            avg("trip_duration_minutes").alias("avg_duration")
        ).collect()[0]
        
        # LGA trips
        lga_trips = self.df.filter(
            (col("pickup_latitude") >= AIRPORT_COORDINATES["LGA"]["lat"] - airport_radius) &
            (col("pickup_latitude") <= AIRPORT_COORDINATES["LGA"]["lat"] + airport_radius) &
            (col("pickup_longitude") >= AIRPORT_COORDINATES["LGA"]["lon"] - airport_radius) &
            (col("pickup_longitude") <= AIRPORT_COORDINATES["LGA"]["lon"] + airport_radius)
        )
        
        lga_stats = lga_trips.agg(
            count("*").alias("trip_count"),
            avg("fare_amount").alias("avg_fare"),
            avg("trip_distance").alias("avg_distance"),
            avg("trip_duration_minutes").alias("avg_duration")
        ).collect()[0]
        
        return {
            "JFK": {
                "trip_count": jfk_stats.trip_count,
                "avg_fare": jfk_stats.avg_fare,
                "avg_distance": jfk_stats.avg_distance,
                "avg_duration": jfk_stats.avg_duration
            },
            "LGA": {
                "trip_count": lga_stats.trip_count,
                "avg_fare": lga_stats.avg_fare,
                "avg_distance": lga_stats.avg_distance,
                "avg_duration": lga_stats.avg_duration
            }
        }
    
    def save_results(self, results: dict, output_file: str = "geospatial_analysis_results.json"):
        """Save analysis results"""
        import json
        
        output_path = OUTPUT_DATA_DIR / output_file
        logger.info(f"Saving results to: {output_path}")
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return output_path


def run_geospatial_analysis(spark: SparkSession, df=None):
    """Run complete geospatial analysis"""
    logger.info("=" * 60)
    logger.info("GEOSPATIAL ANALYSIS")
    logger.info("=" * 60)
    
    analyzer = GeospatialAnalysis(spark)
    if df is None:
        analyzer.load_data()
    else:
        analyzer.df = df
    
    results = {}
    
    # Pickup hotspots
    results["pickup_hotspots"] = analyzer.pickup_hotspots(top_n=20)
    logger.info(f"✅ Pickup hotspots: {len(results['pickup_hotspots'])} locations")
    
    # Dropoff hotspots
    results["dropoff_hotspots"] = analyzer.dropoff_hotspots(top_n=20)
    logger.info(f"✅ Dropoff hotspots: {len(results['dropoff_hotspots'])} locations")
    
    # Route pairs
    results["route_pairs"] = analyzer.route_pairs(top_n=20)
    logger.info(f"✅ Route pairs: {len(results['route_pairs'])} pairs")
    
    # Airport analysis
    results["airport_analysis"] = analyzer.airport_analysis()
    logger.info("✅ Airport analysis complete")
    
    # Save results
    output_path = analyzer.save_results(results)
    logger.info(f"✅ Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    from src.utils.spark_utils import create_spark_session, stop_spark_session
    
    logging.basicConfig(level=logging.INFO)
    
    spark = create_spark_session("Geospatial_Analysis")
    
    try:
        results = run_geospatial_analysis(spark)
        print("✅ Geospatial analysis complete!")
    finally:
        stop_spark_session(spark)

