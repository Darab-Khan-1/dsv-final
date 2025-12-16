"""
Economic Analysis Service
Business logic for economic analysis endpoints
"""

from typing import Dict, Any, Optional
from app.core.spark_session import get_spark_session
from app.core.config import settings
from app.utils.spark_imports import get_spark_functions, get_spark_window, get_spark_ml
from src.config import PROCESSED_DATA_DIR, DATA_DIR
import logging

logger = logging.getLogger(__name__)


class EconomicAnalysisService:
    """Service for economic analysis"""
    
    def __init__(self):
        self._spark = None
        # Use absolute path from backend/src/config.py so API and pipeline share one source of truth
        self.data_path = str(PROCESSED_DATA_DIR / "cleaned_data.parquet")
        # Aggregate table paths for fast queries
        self.aggregates_dir = DATA_DIR / "aggregates"
        self.economic_fare_path = str(self.aggregates_dir / "economic_fare_analysis.parquet")
        self.tip_behavior_path = str(self.aggregates_dir / "tip_behavior_analysis.parquet")
        self.temporal_hourly_path = str(self.aggregates_dir / "temporal_hourly_stats.parquet")
        self.airport_analysis_path = str(self.aggregates_dir / "airport_analysis.parquet")
        self.summary_stats_path = str(self.aggregates_dir / "summary_stats.parquet")
    
    @property
    def spark(self):
        """Lazy Spark session property"""
        if self._spark is None:
            self._spark = get_spark_session()
        return self._spark
    
    async def get_correlations(self) -> Dict[str, Any]:
        """Get correlation matrix"""
        try:
            ml_modules = get_spark_ml()
            VectorAssembler = ml_modules["VectorAssembler"]
            Correlation = ml_modules["Correlation"]
            
            df = self.spark.read.parquet(self.data_path)
            
            # Prepare numeric columns
            numeric_cols = ["fare_amount", "trip_distance", "trip_duration_minutes"]
            assembler = VectorAssembler(inputCols=numeric_cols, outputCol="features")
            df_vector = assembler.transform(df).select("features")
            
            # Calculate correlation
            correlation_matrix = Correlation.corr(df_vector, "features").head()[0]
            corr_array = correlation_matrix.toArray()
            
            return {
                "columns": numeric_cols,
                "correlation_matrix": corr_array.tolist()
            }
        except Exception as e:
            logger.error(f"Error in get_correlations: {e}")
            raise
    
    async def get_tip_analysis(self, group_by: str) -> Dict[str, Any]:
        """Get tip behavior analysis - optimized with aggregate table"""
        try:
            import os
            F = get_spark_functions()
            
            # Try to use aggregate table first
            if os.path.exists(self.tip_behavior_path) and group_by in ["payment_type", "hour"]:
                df_agg = self.spark.read.parquet(self.tip_behavior_path)
                
                if group_by == "payment_type":
                    result = df_agg \
                        .groupBy("payment_type") \
                        .agg(F.avg("tip_percentage").alias("avg_tip_percent")) \
                        .collect()
                    return {
                        "data": [
                            {"payment_type": row.payment_type, "avg_tip_percent": float(row.avg_tip_percent) if row.avg_tip_percent else 0.0}
                            for row in result
                        ]
                    }
                elif group_by == "hour":
                    result = df_agg \
                        .groupBy("pickup_hour") \
                        .agg(F.avg("tip_percentage").alias("avg_tip_percent")) \
                        .orderBy("pickup_hour") \
                        .collect()
                    return {
                        "data": [
                            {"hour": row.pickup_hour, "avg_tip_percent": float(row.avg_tip_percent) if row.avg_tip_percent else 0.0}
                            for row in result
                        ]
                    }
            
            # Fallback to full scan
            df = self.spark.read.parquet(self.data_path)
            df_tip = df.withColumn(
                "tip_percentage",
                F.when(F.col("fare_amount") > 0, (F.col("tip_amount") / F.col("fare_amount")) * 100).otherwise(0)
            )
            
            if group_by == "payment_type":
                result = df_tip \
                    .groupBy("payment_type") \
                    .agg(F.avg("tip_percentage").alias("avg_tip_percent")) \
                    .collect()
                return {
                    "data": [
                        {"payment_type": row.payment_type, "avg_tip_percent": float(row.avg_tip_percent) if row.avg_tip_percent else 0.0}
                        for row in result
                    ]
                }
            elif group_by == "hour":
                result = df_tip \
                    .withColumn("hour", F.hour("tpep_pickup_datetime")) \
                    .groupBy("hour") \
                    .agg(F.avg("tip_percentage").alias("avg_tip_percent")) \
                    .orderBy("hour") \
                    .collect()
                return {
                    "data": [
                        {"hour": row.hour, "avg_tip_percent": float(row.avg_tip_percent) if row.avg_tip_percent else 0.0}
                        for row in result
                    ]
                }
            else:
                return {"message": f"Group by {group_by} not yet implemented"}
        except Exception as e:
            logger.error(f"Error in get_tip_analysis: {e}")
            raise
    
    async def get_revenue_analysis(
        self,
        group_by: str,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get revenue analysis"""
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.data_path)
            
            if year:
                df = df.filter(F.year("tpep_pickup_datetime") == year)
            
            if group_by == "hour":
                result = df \
                    .withColumn("hour", F.hour("tpep_pickup_datetime")) \
                    .groupBy("hour") \
                    .agg(F.avg("total_amount").alias("avg_revenue")) \
                    .orderBy("hour") \
                    .collect()
                return {
                    "data": [
                        {"hour": row.hour, "avg_revenue": row.avg_revenue}
                        for row in result
                    ]
                }
            else:
                return {"message": f"Group by {group_by} not yet implemented"}
        except Exception as e:
            logger.error(f"Error in get_revenue_analysis: {e}")
            raise
    
    async def get_price_elasticity(self) -> Dict[str, Any]:
        """Get price elasticity analysis (fare per mile) - optimized with aggregate table"""
        try:
            import os
            F = get_spark_functions()
            
            # Try to use aggregate table first
            if os.path.exists(self.economic_fare_path):
                df_agg = self.spark.read.parquet(self.economic_fare_path)
                
                # Map distance buckets to match frontend format
                df_mapped = df_agg.withColumn(
                    "distance_bucket",
                    F.when(F.col("distance_bucket") == "0-1mi", "Short (<2 mi)")
                    .when(F.col("distance_bucket") == "1-3mi", "Short (<2 mi)")
                    .when(F.col("distance_bucket") == "3-5mi", "Medium (2-5 mi)")
                    .when(F.col("distance_bucket") == "5-10mi", "Long (5-10 mi)")
                    .otherwise("Very Long (>10 mi)")
                )
                
                result = df_mapped \
                    .groupBy("distance_bucket") \
                    .agg(
                        F.avg("fare_per_mile").alias("avg_fare_per_mile"),
                        F.avg("avg_fare").alias("avg_fare"),
                        F.avg("avg_fare").alias("avg_distance"),  # Using avg_fare as proxy
                        F.sum("trip_count").alias("trip_count")
                    ) \
                    .collect()
            else:
                # Fallback to full scan (slower)
                df = self.spark.read.parquet(self.data_path)
                df_elasticity = df \
                    .filter(F.col("trip_distance") > 0) \
                    .withColumn("fare_per_mile", F.col("fare_amount") / F.col("trip_distance"))
                
                df_bucketed = df_elasticity.withColumn(
                    "distance_bucket",
                    F.when(F.col("trip_distance") < 2, "Short (<2 mi)")
                    .when(F.col("trip_distance") < 5, "Medium (2-5 mi)")
                    .when(F.col("trip_distance") < 10, "Long (5-10 mi)")
                    .otherwise("Very Long (>10 mi)")
                )
                
                result = df_bucketed \
                    .groupBy("distance_bucket") \
                    .agg(
                        F.avg("fare_per_mile").alias("avg_fare_per_mile"),
                        F.avg("fare_amount").alias("avg_fare"),
                        F.avg("trip_distance").alias("avg_distance"),
                        F.count("*").alias("trip_count")
                    ) \
                    .collect()
            
            return {
                "data": [
                    {
                        "distance_bucket": row.distance_bucket,
                        "avg_fare_per_mile": float(row.avg_fare_per_mile) if row.avg_fare_per_mile else 0.0,
                        "avg_fare": float(row.avg_fare) if row.avg_fare else 0.0,
                        "avg_distance": float(row.avg_distance) if row.avg_distance else 0.0,
                        "trip_count": int(row.trip_count) if row.trip_count else 0
                    }
                    for row in result
                ]
            }
        except Exception as e:
            logger.error(f"Error in get_price_elasticity: {e}")
            raise
    
    async def get_surge_pricing(self, threshold: float = 3.0) -> Dict[str, Any]:
        """Detect surge pricing patterns - optimized with sampling"""
        try:
            F = get_spark_functions()
            Window = get_spark_window()
            
            # Use sampling for surge detection (complex calculation)
            df = self.spark.read.parquet(self.data_path)
            df_sample = df.sample(0.1, seed=42)  # 10% sample for performance
            
            # Add grid columns if not present
            if "pickup_lat_grid" not in df_sample.columns:
                df_sample = df_sample \
                    .withColumn("pickup_lat_grid", F.round(F.col("pickup_latitude"), 2)) \
                    .withColumn("pickup_lon_grid", F.round(F.col("pickup_longitude"), 2))
            
            # Calculate z-scores by hour and zone
            window_spec = Window.partitionBy("pickup_hour", "pickup_lat_grid", "pickup_lon_grid")
            
            df_with_stats = df_sample \
                .withColumn("zone_avg_fare", F.avg("fare_amount").over(window_spec)) \
                .withColumn("zone_std_fare", F.stddev("fare_amount").over(window_spec))
            
            # Calculate z-score, handling division by zero when stddev is 0
            # If stddev is 0 or null, set z_score to 0 (no variation = no surge)
            df_surge = df_with_stats \
                .withColumn("z_score", 
                    F.when(
                        (F.col("zone_std_fare").isNull()) | (F.col("zone_std_fare") == 0),
                        0.0
                    ).otherwise(
                        (F.col("fare_amount") - F.col("zone_avg_fare")) / F.col("zone_std_fare")
                    )
                ) \
                .filter(F.abs(F.col("z_score")) > threshold)
            
            # Aggregate surge events
            surge_summary = df_surge \
                .withColumn("hour", F.hour("tpep_pickup_datetime")) \
                .groupBy("hour") \
                .agg(
                    F.count("*").alias("surge_count"),
                    F.avg("fare_amount").alias("avg_surge_fare"),
                    F.avg("z_score").alias("avg_z_score")
                ) \
                .orderBy(F.desc("surge_count")) \
                .limit(10) \
                .collect()
            
            total_surge = df_surge.count()
            total_trips_sample = df_sample.count()
            total_surge_scaled = total_surge * 10  # Scale up since we sampled 10%
            
            return {
                "total_surge_events": int(total_surge_scaled),
                "surge_percentage": (total_surge / total_trips_sample) * 100 if total_trips_sample > 0 else 0,
                "top_surge_hours": [
                    {
                        "hour": row.hour,
                        "surge_count": row.surge_count,
                        "avg_surge_fare": row.avg_surge_fare,
                        "avg_z_score": row.avg_z_score
                    }
                    for row in surge_summary
                ],
                "threshold": threshold
            }
        except Exception as e:
            logger.error(f"Error in get_surge_pricing: {e}")
            raise
    
    async def get_economic_insights(self) -> Dict[str, Any]:
        """Get key economic insights for dashboard - optimized with aggregate tables"""
        try:
            import os
            F = get_spark_functions()
            from src.config import AIRPORT_COORDINATES
            
            # 1. Highest Tip Hour - use tip_behavior_analysis aggregate table
            if os.path.exists(self.tip_behavior_path):
                df_tip = self.spark.read.parquet(self.tip_behavior_path)
                tip_by_hour = df_tip \
                    .groupBy("pickup_hour") \
                    .agg(F.avg("tip_percentage").alias("avg_tip_percent")) \
                    .orderBy(F.desc("avg_tip_percent")) \
                    .limit(1) \
                    .collect()
                highest_tip_hour = tip_by_hour[0].pickup_hour if tip_by_hour else None
                highest_tip_percent = float(tip_by_hour[0].avg_tip_percent) if tip_by_hour else 0.0
            else:
                # Fallback: use temporal_hourly_stats
                if os.path.exists(self.temporal_hourly_path):
                    df_temporal = self.spark.read.parquet(self.temporal_hourly_path)
                    # Calculate tip percentage from avg_tip and avg_fare
                    tip_by_hour = df_temporal \
                        .withColumn("tip_percentage", 
                            F.when(F.col("avg_fare") > 0, (F.col("avg_tip") / F.col("avg_fare")) * 100).otherwise(0)
                        ) \
                        .groupBy("pickup_hour") \
                        .agg(F.avg("tip_percentage").alias("avg_tip_percent")) \
                        .orderBy(F.desc("avg_tip_percent")) \
                        .limit(1) \
                        .collect()
                    highest_tip_hour = tip_by_hour[0].pickup_hour if tip_by_hour else None
                    highest_tip_percent = float(tip_by_hour[0].avg_tip_percent) if tip_by_hour else 0.0
                else:
                    highest_tip_hour = None
                    highest_tip_percent = 0.0
            
            # 2. Best Revenue Hour - use temporal_hourly_stats
            if os.path.exists(self.temporal_hourly_path):
                df_temporal = self.spark.read.parquet(self.temporal_hourly_path)
                revenue_by_hour = df_temporal \
                    .groupBy("pickup_hour") \
                    .agg(F.avg("avg_fare").alias("avg_fare")) \
                    .orderBy(F.desc("avg_fare")) \
                    .limit(1) \
                    .collect()
                best_revenue_hour = revenue_by_hour[0].pickup_hour if revenue_by_hour else None
            else:
                best_revenue_hour = None
            
            # 3. Airport Premium - use airport_analysis aggregate table
            if os.path.exists(self.airport_analysis_path):
                df_airport = self.spark.read.parquet(self.airport_analysis_path)
                airport_avg = df_airport.agg(F.avg("avg_fare").alias("avg_fare")).collect()[0]
                airport_avg_fare = float(airport_avg.avg_fare) if airport_avg.avg_fare else 0.0
            else:
                airport_avg_fare = 0.0
            
            # City average from summary stats
            if os.path.exists(self.summary_stats_path):
                df_summary = self.spark.read.parquet(self.summary_stats_path)
                city_avg_row = df_summary.collect()[0]
                city_avg_fare = float(city_avg_row.avg_fare) if city_avg_row.avg_fare else 0.0
            else:
                city_avg_fare = 0.0
            
            airport_premium = ((airport_avg_fare - city_avg_fare) / city_avg_fare * 100) if city_avg_fare > 0 else 0.0
            
            # 4. Credit Card Tip vs Cash Tip - use tip_behavior_analysis
            if os.path.exists(self.tip_behavior_path):
                df_tip = self.spark.read.parquet(self.tip_behavior_path)
                credit_tips = df_tip.filter(F.col("payment_type") == 1) \
                    .agg(F.avg("tip_percentage").alias("avg_tip_percent")).collect()[0]
                cash_tips = df_tip.filter(F.col("payment_type") == 2) \
                    .agg(F.avg("tip_percentage").alias("avg_tip_percent")).collect()[0]
                credit_tip_rate = float(credit_tips.avg_tip_percent) if credit_tips.avg_tip_percent else 0.0
                cash_tip_rate = float(cash_tips.avg_tip_percent) if cash_tips.avg_tip_percent else 0.0
            else:
                credit_tip_rate = 0.0
                cash_tip_rate = 0.0
            
            credit_card_premium = (credit_tip_rate - cash_tip_rate) if cash_tip_rate > 0 else 0.0
            
            return {
                "highest_tip_hour": int(highest_tip_hour) if highest_tip_hour is not None else None,
                "highest_tip_percent": highest_tip_percent,
                "best_revenue_hour": int(best_revenue_hour) if best_revenue_hour is not None else None,
                "airport_premium": airport_premium,
                "credit_card_tip_premium": credit_card_premium,
                "credit_tip_rate": credit_tip_rate,
                "cash_tip_rate": cash_tip_rate
            }
        except Exception as e:
            logger.error(f"Error in get_economic_insights: {e}")
            raise
    
    async def get_customer_segments(self, n_segments: int = 5) -> Dict[str, Any]:
        """Get customer segmentation based on spending behavior"""
        try:
            F = get_spark_functions()
            ml_modules = get_spark_ml()
            KMeans = ml_modules["KMeans"]
            VectorAssembler = ml_modules["VectorAssembler"]
            StandardScaler = ml_modules["StandardScaler"]
            
            df = self.spark.read.parquet(self.data_path)
            
            # Sample for performance
            df_sample = df.sample(0.15, seed=42)  # 15% sample (increased for better analysis with more RAM)
            
            # Prepare features for clustering
            assembler = VectorAssembler(
                inputCols=["fare_amount", "trip_distance", "trip_duration_minutes"],
                outputCol="features"
            )
            df_features = assembler.transform(df_sample)
            
            # Scale features
            scaler = StandardScaler(
                inputCol="features",
                outputCol="scaled_features",
                withStd=True,
                withMean=True
            )
            scaler_model = scaler.fit(df_features)
            df_scaled = scaler_model.transform(df_features)
            
            # K-Means clustering
            kmeans = KMeans(k=n_segments, seed=42, featuresCol="scaled_features", predictionCol="segment")
            model = kmeans.fit(df_scaled)
            df_segmented = model.transform(df_scaled)
            
            # Get segment characteristics
            segment_stats = df_segmented.groupBy("segment").agg(
                F.count("*").alias("customer_count"),
                F.avg("fare_amount").alias("avg_fare"),
                F.avg("trip_distance").alias("avg_distance"),
                F.avg("trip_duration_minutes").alias("avg_duration")
            ).orderBy("segment").collect()
            
            return {
                "segments": [
                    {
                        "segment_id": row.segment,
                        "customer_count": row.customer_count,
                        "avg_fare": row.avg_fare,
                        "avg_distance": row.avg_distance,
                        "avg_duration": row.avg_duration
                    }
                    for row in segment_stats
                ],
                "n_segments": n_segments
            }
        except Exception as e:
            logger.error(f"Error in get_customer_segments: {e}")
            raise
    
    async def get_market_share(self) -> Dict[str, Any]:
        """Get vendor market share - optimized with sampling for large datasets"""
        try:
            import os
            F = get_spark_functions()
            
            # Use aggregate table if available (economic_fare_analysis has payment_type, but we need VendorID)
            # For now, use sampling to speed up
            df = self.spark.read.parquet(self.data_path)
            
            # Sample 10% for market share calculation (vendors are limited, so sampling is safe)
            df_sample = df.sample(0.1, seed=42)
            
            result = df_sample \
                .groupBy("VendorID") \
                .agg(
                    F.count("*").alias("trip_count"),
                    F.avg("fare_amount").alias("avg_fare")
                ) \
                .collect()
            
            total_trips = sum(row.trip_count for row in result)
            
            return {
                "data": [
                    {
                        "vendor_id": int(row.VendorID) if row.VendorID else 0,
                        "trip_count": int(row.trip_count),
                        "market_share_percent": float((row.trip_count / total_trips) * 100) if total_trips > 0 else 0.0,
                        "avg_fare": float(row.avg_fare) if row.avg_fare else 0.0
                    }
                    for row in result
                ],
                "total_trips": int(total_trips)
            }
        except Exception as e:
            logger.error(f"Error in get_market_share: {e}")
            raise

