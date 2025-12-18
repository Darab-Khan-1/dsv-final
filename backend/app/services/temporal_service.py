from typing import Optional, Dict, Any
import logging

from app.core.spark_session import get_spark_session
from app.utils.spark_imports import get_spark_functions, get_spark_window
from src.config import PROCESSED_DATA_DIR, DATA_DIR

logger = logging.getLogger(__name__)


class TemporalAnalysisService:
    def __init__(self):
        self._spark = None
        self.data_path = str(PROCESSED_DATA_DIR / "cleaned_data.parquet")
        self.temporal_agg_path = str(DATA_DIR / "aggregates" / "temporal_hourly_stats.parquet")
    
    @property
    def spark(self):
        if self._spark is None:
            self._spark = get_spark_session()
        return self._spark
    
    async def get_trips_by_hour(
        self, 
        year: Optional[int] = None,
        month: Optional[int] = None,
        day_of_week: Optional[int] = None
    ) -> Dict[str, Any]:
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.temporal_agg_path)

            if year is not None:
                df = df.filter(F.col("pickup_year") == int(year))
            if month is not None:
                df = df.filter(F.col("pickup_month") == int(month))
            if day_of_week is not None:
                df = df.filter(F.col("pickup_day_of_week") == int(day_of_week))

            result = (
                df.groupBy("pickup_hour")
                .agg(F.sum("trip_count").alias("trip_count"))
                .orderBy("pickup_hour")
                .collect()
            )
            
            return {
                "data": [{"hour": row.pickup_hour, "trip_count": row.trip_count} for row in result]
            }
        except Exception as e:
            logger.error(f"Error in get_trips_by_hour: {e}")
            raise
    
    async def get_trips_by_day(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.temporal_agg_path)

            if year is not None:
                df = df.filter(F.col("pickup_year") == int(year))
            if month is not None:
                df = df.filter(F.col("pickup_month") == int(month))

            result = (
                df.groupBy("pickup_day_of_week")
                .agg(F.sum("trip_count").alias("trip_count"))
                .orderBy("pickup_day_of_week")
                .collect()
            )
            
            return {
                "data": [{"day_of_week": row.pickup_day_of_week, "trip_count": row.trip_count} for row in result]
            }
        except Exception as e:
            logger.error(f"Error in get_trips_by_day: {e}")
            raise
    
    async def get_trips_by_month(
        self,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.data_path)
            
            if year:
                df = df.filter(F.year("tpep_pickup_datetime") == year)
            
            result = df \
                .withColumn("month", F.month("tpep_pickup_datetime")) \
                .withColumn("year", F.year("tpep_pickup_datetime")) \
                .groupBy("year", "month") \
                .agg(F.count("*").alias("trip_count")) \
                .orderBy("year", "month") \
                .collect()
            
            return {
                "data": [{"year": row.year, "month": row.month, "trip_count": row.trip_count} for row in result]
            }
        except Exception as e:
            logger.error(f"Error in get_trips_by_month: {e}")
            raise
    
    async def get_peak_hours(self, top_n: int = 10) -> Dict[str, Any]:
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.temporal_agg_path)

            result = (
                df.groupBy("pickup_hour")
                .agg(F.sum("trip_count").alias("trip_count"))
                .orderBy(F.desc("trip_count"))
                .limit(top_n)
                .collect()
            )
            
            return {
                "data": [{"hour": row.pickup_hour, "trip_count": row.trip_count} for row in result]
            }
        except Exception as e:
            logger.error(f"Error in get_peak_hours: {e}")
            raise
    
    async def get_duration_distribution(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.data_path)
            
            if year:
                df = df.filter(F.year("tpep_pickup_datetime") == year)
            if month:
                df = df.filter(F.month("tpep_pickup_datetime") == month)
            
            stats = df.agg(
                F.avg("trip_duration_minutes").alias("mean"),
                F.stddev("trip_duration_minutes").alias("stddev"),
                F.min("trip_duration_minutes").alias("min"),
                F.max("trip_duration_minutes").alias("max"),
                F.percentile_approx("trip_duration_minutes", 0.5).alias("median"),
                F.percentile_approx("trip_duration_minutes", 0.25).alias("p25"),
                F.percentile_approx("trip_duration_minutes", 0.75).alias("p75")
            ).collect()[0]
            
            return {
                "mean": stats.mean,
                "stddev": stats.stddev,
                "min": stats.min,
                "max": stats.max,
                "median": stats.median,
                "p25": stats.p25,
                "p75": stats.p75
            }
        except Exception as e:
            logger.error(f"Error in get_duration_distribution: {e}")
            raise
    
    async def get_fare_trends(
        self,
        group_by: str = "month",
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.data_path)
            
            if year:
                df = df.filter(F.year("tpep_pickup_datetime") == year)
            
            if group_by == "hour":
                result = df \
                    .withColumn("hour", F.hour("tpep_pickup_datetime")) \
                    .groupBy("hour") \
                    .agg(F.avg("fare_amount").alias("avg_fare")) \
                    .orderBy("hour") \
                    .collect()
                return {"data": [{"hour": row.hour, "avg_fare": row.avg_fare} for row in result]}
            elif group_by == "day":
                result = df \
                    .withColumn("day_of_week", F.dayofweek("tpep_pickup_datetime")) \
                    .groupBy("day_of_week") \
                    .agg(F.avg("fare_amount").alias("avg_fare")) \
                    .orderBy("day_of_week") \
                    .collect()
                return {"data": [{"day_of_week": row.day_of_week, "avg_fare": row.avg_fare} for row in result]}
            else:
                result = df \
                    .withColumn("month", F.month("tpep_pickup_datetime")) \
                    .withColumn("year", F.year("tpep_pickup_datetime")) \
                    .groupBy("year", "month") \
                    .agg(F.avg("fare_amount").alias("avg_fare")) \
                    .orderBy("year", "month") \
                    .collect()
                return {"data": [{"year": row.year, "month": row.month, "avg_fare": row.avg_fare} for row in result]}
        except Exception as e:
            logger.error(f"Error in get_fare_trends: {e}")
            raise
    
    async def get_time_series_decomposition(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            F = get_spark_functions()
            Window = get_spark_window()
            df = self.spark.read.parquet(self.data_path)
            
            if start_date:
                df = df.filter(F.col("tpep_pickup_datetime") >= start_date)
            if end_date:
                df = df.filter(F.col("tpep_pickup_datetime") <= end_date)
            
            daily_trips = df \
                .withColumn("date", F.date_format("tpep_pickup_datetime", "yyyy-MM-dd")) \
                .groupBy("date") \
                .agg(F.count("*").alias("trip_count")) \
                .orderBy("date") \
                .limit(365)
            
            window_spec = Window.orderBy("date").rowsBetween(-6, 0)
            daily_trips = daily_trips.withColumn("trend", F.avg("trip_count").over(window_spec))
            
            df_with_dow = df \
                .withColumn("day_of_week", F.dayofweek("tpep_pickup_datetime")) \
                .withColumn("date", F.date_format("tpep_pickup_datetime", "yyyy-MM-dd"))
            
            seasonal = df_with_dow \
                .groupBy("day_of_week") \
                .agg(F.avg("trip_count").alias("seasonal_component")) \
                .collect()
            
            result = daily_trips.collect()
            
            return {
                "data": [
                    {
                        "date": row.date,
                        "trip_count": row.trip_count,
                        "trend": row.trend if hasattr(row, 'trend') else None
                    }
                    for row in result[:30]
                ],
                "seasonal": [
                    {"day_of_week": row.day_of_week, "avg_trips": row.seasonal_component}
                    for row in seasonal
                ],
                "message": "Time series decomposition (simplified version)"
            }
        except Exception as e:
            logger.error(f"Error in get_time_series_decomposition: {e}")
            raise

