"""
Data Service
Business logic for data endpoints
"""

from typing import Dict, Any, Optional
import logging

from app.core.spark_session import get_spark_session
from app.utils.spark_imports import get_spark_functions
from src.config import PROCESSED_DATA_DIR, DATA_DIR

logger = logging.getLogger(__name__)


class DataService:
    """Service for data operations"""
    
    def __init__(self):
        self._spark = None
        # Use absolute path from backend/src/config.py so API and pipeline share one source of truth
        self.data_path = str(PROCESSED_DATA_DIR / "cleaned_data.parquet")
        # Pre-computed summary stats for fast API responses
        self.summary_stats_path = str(DATA_DIR / "aggregates" / "summary_stats.parquet")
    
    @property
    def spark(self):
        """Lazy Spark session property"""
        if self._spark is None:
            self._spark = get_spark_session()
        return self._spark
    
    async def get_data_summary(self) -> Dict[str, Any]:
        """Get dataset summary statistics from pre-computed aggregate table"""
        try:
            import os
            # Try to use pre-computed summary stats first (much faster)
            if os.path.exists(self.summary_stats_path):
                df_summary = self.spark.read.parquet(self.summary_stats_path)
                row = df_summary.collect()[0]
                
                # Calculate economic metrics (with fallback calculation if columns don't exist)
                try:
                    total_revenue = float(row.total_revenue) if row.total_revenue is not None else 0.0
                except (AttributeError, KeyError):
                    # Calculate from avg_fare * total_records if total_revenue column doesn't exist
                    total_revenue = float(row.avg_fare) * int(row.total_records) if row.avg_fare is not None else 0.0
                
                try:
                    avg_fare_per_mile = float(row.avg_fare_per_mile) if row.avg_fare_per_mile is not None else 0.0
                except (AttributeError, KeyError):
                    # Calculate from avg_fare / avg_distance if column doesn't exist
                    if row.avg_distance and row.avg_distance > 0 and row.avg_fare:
                        avg_fare_per_mile = float(row.avg_fare) / float(row.avg_distance)
                    else:
                        avg_fare_per_mile = 0.0
                
                try:
                    avg_tip_rate = float(row.avg_tip_rate) if row.avg_tip_rate is not None else 0.0
                except (AttributeError, KeyError):
                    # Calculate from avg_tip / avg_fare if column doesn't exist
                    if row.avg_fare and row.avg_fare > 0 and row.avg_tip:
                        avg_tip_rate = (float(row.avg_tip) / float(row.avg_fare)) * 100
                    else:
                        avg_tip_rate = 0.0
                
                return {
                    "total_records": row.total_records,
                    "date_range": {
                        "start": str(row.min_date),
                        "end": str(row.max_date)
                    },
                    "economic_metrics": {
                        "total_revenue": total_revenue,
                        "avg_fare_per_mile": avg_fare_per_mile,
                        "avg_tip_rate": avg_tip_rate,
                    },
                    "summary": {
                        "mean": {
                            "fare_amount": float(row.avg_fare) if row.avg_fare is not None else 0.0,
                            "trip_distance": float(row.avg_distance) if row.avg_distance is not None else 0.0,
                            "trip_duration_minutes": float(row.avg_duration) if row.avg_duration is not None else 0.0,
                            "tip_amount": float(row.avg_tip) if row.avg_tip is not None else 0.0,
                            "passenger_count": float(row.avg_passengers) if row.avg_passengers is not None else 0.0,
                        },
                        "min": {
                            "fare_amount": float(row.min_fare) if row.min_fare is not None else 0.0,
                            "trip_distance": float(row.min_distance) if row.min_distance is not None else 0.0,
                            "trip_duration_minutes": float(row.min_duration) if row.min_duration is not None else 0.0,
                            "tip_amount": float(row.min_tip) if row.min_tip is not None else 0.0,
                            "passenger_count": int(row.min_passengers) if row.min_passengers is not None else 0,
                        },
                        "max": {
                            "fare_amount": float(row.max_fare) if row.max_fare is not None else 0.0,
                            "trip_distance": float(row.max_distance) if row.max_distance is not None else 0.0,
                            "trip_duration_minutes": float(row.max_duration) if row.max_duration is not None else 0.0,
                            "tip_amount": float(row.max_tip) if row.max_tip is not None else 0.0,
                            "passenger_count": int(row.max_passengers) if row.max_passengers is not None else 0,
                        },
                        "stddev": {
                            "fare_amount": float(row.stddev_fare) if row.stddev_fare is not None else 0.0,
                            "trip_distance": float(row.stddev_distance) if row.stddev_distance is not None else 0.0,
                            "trip_duration_minutes": float(row.stddev_duration) if row.stddev_duration is not None else 0.0,
                        },
                        "count": {
                            "fare_amount": row.total_records,
                            "trip_distance": row.total_records,
                            "trip_duration_minutes": row.total_records,
                            "tip_amount": row.total_records,
                            "passenger_count": row.total_records,
                        },
                    }
                }
            
            # Fallback to full dataset scan if aggregate table doesn't exist
            if not os.path.exists(self.data_path):
                raise FileNotFoundError(
                    f"Processed data file not found: {self.data_path}\n"
                    f"Please run the data processing pipeline first:\n"
                    f"  cd backend && python3 main.py\n"
                    f"Or use: ./process_data.sh"
                )
            F = get_spark_functions()
            df = self.spark.read.parquet(self.data_path)
            
            total_count = df.count()
            
            summary = df.describe().collect()
            
            date_range = df.agg(
                F.min("tpep_pickup_datetime").alias("min_date"),
                F.max("tpep_pickup_datetime").alias("max_date")
            ).collect()[0]
            
            return {
                "total_records": total_count,
                "date_range": {
                    "start": str(date_range.min_date),
                    "end": str(date_range.max_date)
                },
                "summary": {
                    row.summary: {
                        col: row[col] 
                        for col in df.columns 
                        if col in row.asDict()
                    }
                    for row in summary
                }
            }
        except Exception as e:
            logger.error(f"Error in get_data_summary: {e}")
            raise
    
    async def get_data_sample(
        self,
        n: int = 100,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get sample data"""
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.data_path)
            
            if year:
                df = df.filter(F.year("tpep_pickup_datetime") == year)
            if month:
                df = df.filter(F.month("tpep_pickup_datetime") == month)
            
            sample = df.limit(n).toPandas()
            
            return {
                "count": len(sample),
                "data": sample.to_dict(orient="records")
            }
        except Exception as e:
            logger.error(f"Error in get_data_sample: {e}")
            raise
    
    async def get_paginated_data(
        self,
        page: int = 1,
        page_size: int = 100,
        year: Optional[int] = None,
        month: Optional[int] = None,
        payment_type: Optional[int] = None,
        min_fare: Optional[float] = None,
        max_fare: Optional[float] = None,
        min_distance: Optional[float] = None,
        max_distance: Optional[float] = None,
        min_passengers: Optional[int] = None,
        max_passengers: Optional[int] = None,
        order_by: Optional[str] = None,
        order_direction: str = "asc"
    ) -> Dict[str, Any]:
        """Get paginated data using Spark SQL - optimized for performance"""
        try:
            import os
            F = get_spark_functions()
            
            # Use partition pruning when filtering by year/month
            # Spark will automatically use partition pruning if data is partitioned by year/month
            df = self.spark.read.parquet(self.data_path)
            
            # Apply filters - Spark will use partition pruning automatically if data is partitioned
            # Using partition columns directly enables efficient partition pruning
            if year:
                df = df.filter(F.col("year") == year)
            if month:
                df = df.filter(F.col("month") == month)
            
            # Apply additional filters for better performance
            if payment_type is not None:
                df = df.filter(F.col("payment_type") == payment_type)
            if min_fare is not None:
                df = df.filter(F.col("fare_amount") >= min_fare)
            if max_fare is not None:
                df = df.filter(F.col("fare_amount") <= max_fare)
            if min_distance is not None:
                df = df.filter(F.col("trip_distance") >= min_distance)
            if max_distance is not None:
                df = df.filter(F.col("trip_distance") <= max_distance)
            if min_passengers is not None:
                df = df.filter(F.col("passenger_count") >= min_passengers)
            if max_passengers is not None:
                df = df.filter(F.col("passenger_count") <= max_passengers)
            
            # Note: Partition pruning happens at read time, so even if window function is unpartitioned,
            # it operates on a much smaller dataset when filters are applied
            
            # Optimize total count calculation
            # Use summary stats if no filters applied (much faster)
            total_count = None
            if not year and not month:
                # Try to use cached count from summary stats
                if os.path.exists(self.summary_stats_path):
                    try:
                        df_summary = self.spark.read.parquet(self.summary_stats_path)
                        total_count = df_summary.select("total_records").collect()[0].total_records
                    except Exception as e:
                        logger.warning(f"Could not read total count from summary stats: {e}")
            
            # If we don't have cached count, we'll estimate or skip count for better performance
            # For filtered queries, count can be expensive - we'll calculate it lazily
            # or estimate based on filters
            if total_count is None:
                # For filtered queries, we can estimate or calculate
                # But to avoid blocking, let's make count optional for now
                # Calculate count only if dataset is reasonably sized
                try:
                    # Use approximate count if available, otherwise full count
                    # For better UX, we can return estimated count or skip it
                    total_count = df.count()
                except Exception as e:
                    logger.warning(f"Could not calculate total count: {e}")
                    # Use a large estimate to allow pagination
                    total_count = 1000000  # Fallback estimate
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Apply ordering if specified
            order_column = "tpep_pickup_datetime"  # Default
            if order_by and order_by in df.columns:
                order_column = order_by
            
            # Optimize: For first page, no need for window function
            if page == 1:
                # Simple case: just order and limit
                if order_direction.lower() == "desc":
                    df = df.orderBy(F.col(order_column).desc())
                else:
                    df = df.orderBy(F.col(order_column).asc())
                
                page_df = df.limit(page_size)
            else:
                # For other pages, use a more efficient approach
                # Instead of window function on entire dataset, use partitioned window when possible
                from pyspark.sql.window import Window
                
                # Always use partitioning when year/month columns exist to avoid single partition shuffle
                # This is critical for performance - partitioning prevents moving all data to one partition
                partition_cols = []
                if "year" in df.columns:
                    partition_cols.append("year")
                if "month" in df.columns and (month is not None or year is not None):
                    # Include month in partition if column exists and we have some filter context
                    partition_cols.append("month")
                
                # Build partitioned window - this is much faster than unpartitioned
                if partition_cols:
                    if order_direction.lower() == "desc":
                        window = Window.partitionBy(*partition_cols).orderBy(F.col(order_column).desc())
                    else:
                        window = Window.partitionBy(*partition_cols).orderBy(F.col(order_column).asc())
                else:
                    # Fallback: unpartitioned window (slower - should rarely happen)
                    logger.warning("No partition columns available for window function - performance may be degraded")
                    if order_direction.lower() == "desc":
                        window = Window.orderBy(F.col(order_column).desc())
                    else:
                        window = Window.orderBy(F.col(order_column).asc())
                
                # Apply ordering first
                if order_direction.lower() == "desc":
                    df = df.orderBy(F.col(order_column).desc())
                else:
                    df = df.orderBy(F.col(order_column).asc())
                
                # Add row number with partitioned window
                df = df.withColumn("_row_num", F.row_number().over(window))
                
                # Filter for the page
                page_df = df.filter(
                    (F.col("_row_num") > offset) & 
                    (F.col("_row_num") <= offset + page_size)
                ).drop("_row_num")
            
            # Select only needed columns to reduce data transfer
            # Get the page of data - limit the columns to essential ones for performance
            essential_columns = [
                "VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
                "passenger_count", "trip_distance", "fare_amount", "tip_amount",
                "total_amount", "payment_type", "trip_duration_minutes"
            ]
            available_columns = [col for col in essential_columns if col in page_df.columns]
            page_df = page_df.select(available_columns)
            
            # Convert to pandas (limit to reasonable size)
            page_data = page_df.limit(page_size).toPandas()
            
            # Convert to records more efficiently
            records = page_data.to_dict(orient="records")
            
            # Clean up numpy types
            for record in records:
                for key, value in record.items():
                    if hasattr(value, 'item'):
                        record[key] = value.item()
                    elif hasattr(value, 'tolist'):
                        record[key] = value.tolist()
                    elif value is None:
                        record[key] = None
            
            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
            
            return {
                "data": records,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": int(total_count),
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
            }
        except Exception as e:
            logger.error(f"Error in get_paginated_data: {e}")
            raise
    
    async def get_date_range(self) -> Dict[str, Any]:
        """Get available date range - optimized to use summary stats"""
        try:
            import os
            F = get_spark_functions()
            
            # Try to use summary stats first (much faster)
            if os.path.exists(self.summary_stats_path):
                try:
                    df_summary = self.spark.read.parquet(self.summary_stats_path)
                    row = df_summary.collect()[0]
                    min_date_str = str(row.min_date)
                    max_date_str = str(row.max_date)
                    return {
                        "min_date": min_date_str,
                        "max_date": max_date_str,
                        "min_year": int(min_date_str[:4]) if min_date_str else 2015,
                        "max_year": int(max_date_str[:4]) if max_date_str else 2016
                    }
                except Exception as e:
                    logger.warning(f"Could not read date range from summary stats: {e}")
            
            # Fallback to full scan
            df = self.spark.read.parquet(self.data_path)
            
            date_range = df.agg(
                F.min("tpep_pickup_datetime").alias("min_date"),
                F.max("tpep_pickup_datetime").alias("max_date"),
                F.min(F.year("tpep_pickup_datetime")).alias("min_year"),
                F.max(F.year("tpep_pickup_datetime")).alias("max_year")
            ).collect()[0]
            
            return {
                "min_date": str(date_range.min_date),
                "max_date": str(date_range.max_date),
                "min_year": date_range.min_year,
                "max_year": date_range.max_year
            }
        except Exception as e:
            logger.error(f"Error in get_date_range: {e}")
            raise
    
    async def get_distribution(
        self,
        field: str,
        bins: int = 20,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get distribution histogram data for a field"""
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.data_path)
            
            if year:
                df = df.filter(F.year("tpep_pickup_datetime") == year)
            if month:
                df = df.filter(F.month("tpep_pickup_datetime") == month)
            
            # Get min/max for binning
            stats_row = df.agg(
                F.min(field).alias("min_val"),
                F.max(field).alias("max_val")
            ).collect()[0]
            
            # Convert Row to dict to avoid serialization issues
            stats = stats_row.asDict()
            min_val = float(stats["min_val"]) if stats["min_val"] is not None else 0.0
            max_val = float(stats["max_val"]) if stats["max_val"] is not None else 1.0
            
            bin_width = (max_val - min_val) / bins if max_val > min_val else 1.0
            
            # Create bins and count
            df_with_bins = df.withColumn(
                "bin",
                F.floor((F.col(field) - min_val) / bin_width).cast("int")
            ).filter(F.col("bin") >= 0).filter(F.col("bin") < bins)
            
            histogram_rows = df_with_bins.groupBy("bin").count().orderBy("bin").collect()
            
            # Format as histogram data - convert Row objects to dicts
            histogram_data = []
            for row in histogram_rows:
                row_dict = row.asDict()
                bin_num = int(row_dict["bin"])
                count = int(row_dict["count"])
                bin_start = min_val + (bin_num * bin_width)
                bin_end = min_val + ((bin_num + 1) * bin_width)
                histogram_data.append({
                    "bin_start": round(bin_start, 2),
                    "bin_end": round(bin_end, 2),
                    "count": count,
                    "label": f"{round(bin_start, 1)}-{round(bin_end, 1)}"
                })
            
            return {
                "field": field,
                "bins": bins,
                "min": min_val,
                "max": max_val,
                "data": histogram_data
            }
        except Exception as e:
            logger.error(f"Error in get_distribution: {e}")
            raise
    
    async def get_scatter_data(
        self,
        x_field: str,
        y_field: str,
        sample_size: int = 1000,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get scatter plot data (sampled for performance)"""
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.data_path)
            
            if year:
                df = df.filter(F.year("tpep_pickup_datetime") == year)
            if month:
                df = df.filter(F.month("tpep_pickup_datetime") == month)
            
            # Sample data for scatter plot
            total_count = df.count()
            if total_count == 0:
                return {
                    "x_field": x_field,
                    "y_field": y_field,
                    "sample_size": 0,
                    "data": []
                }
            
            sample_fraction = min(sample_size / total_count, 1.0)
            sample_df = df.select(x_field, y_field).sample(False, sample_fraction, seed=42).limit(sample_size)
            sample_pandas = sample_df.toPandas()
            
            # Convert to dict and ensure all values are native Python types
            scatter_data = []
            for _, row in sample_pandas.iterrows():
                scatter_data.append({
                    x_field: float(row[x_field]) if row[x_field] is not None else 0.0,
                    y_field: float(row[y_field]) if row[y_field] is not None else 0.0
                })
            
            return {
                "x_field": x_field,
                "y_field": y_field,
                "sample_size": len(scatter_data),
                "data": scatter_data
            }
        except Exception as e:
            logger.error(f"Error in get_scatter_data: {e}")
            raise

