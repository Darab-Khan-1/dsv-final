from typing import Dict, Any, Optional
import logging

from app.core.spark_session import get_spark_session
from app.utils.spark_imports import get_spark_functions
from src.config import PROCESSED_DATA_DIR, DATA_DIR

logger = logging.getLogger(__name__)


class DataService:
    def __init__(self):
        self._spark = None
        self.data_path = str(PROCESSED_DATA_DIR / "cleaned_data.parquet")
        self.summary_stats_path = str(DATA_DIR / "aggregates" / "summary_stats.parquet")
    
    @property
    def spark(self):
        if self._spark is None:
            self._spark = get_spark_session()
        return self._spark
    
    async def get_data_summary(self) -> Dict[str, Any]:
        try:
            import os
            if os.path.exists(self.summary_stats_path):
                df_summary = self.spark.read.parquet(self.summary_stats_path)
                row = df_summary.collect()[0]
                
                try:
                    total_revenue = float(row.total_revenue) if row.total_revenue is not None else 0.0
                except (AttributeError, KeyError):
                    total_revenue = float(row.avg_fare) * int(row.total_records) if row.avg_fare is not None else 0.0
                
                try:
                    avg_fare_per_mile = float(row.avg_fare_per_mile) if row.avg_fare_per_mile is not None else 0.0
                except (AttributeError, KeyError):
                    if row.avg_distance and row.avg_distance > 0 and row.avg_fare:
                        avg_fare_per_mile = float(row.avg_fare) / float(row.avg_distance)
                    else:
                        avg_fare_per_mile = 0.0
                
                try:
                    avg_tip_rate = float(row.avg_tip_rate) if row.avg_tip_rate is not None else 0.0
                except (AttributeError, KeyError):
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
        try:
            import os
            F = get_spark_functions()
            
            df = self.spark.read.parquet(self.data_path)
            
            if year:
                df = df.filter(F.col("year") == year)
            if month:
                df = df.filter(F.col("month") == month)
            
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
            
            
            total_count = None
            if not year and not month:
                if os.path.exists(self.summary_stats_path):
                    try:
                        df_summary = self.spark.read.parquet(self.summary_stats_path)
                        total_count = df_summary.select("total_records").collect()[0].total_records
                    except Exception as e:
                        logger.warning(f"Could not read total count from summary stats: {e}")
            
            if total_count is None:
                try:
                    total_count = df.count()
                except Exception as e:
                    logger.warning(f"Could not calculate total count: {e}")
                    total_count = 1000000
            
            offset = (page - 1) * page_size
            
            order_column = "tpep_pickup_datetime"
            if order_by and order_by in df.columns:
                order_column = order_by
            
            if page == 1:
                if order_direction.lower() == "desc":
                    df = df.orderBy(F.col(order_column).desc())
                else:
                    df = df.orderBy(F.col(order_column).asc())
                
                page_df = df.limit(page_size)
            else:
                from pyspark.sql.window import Window
                
                partition_cols = []
                if "year" in df.columns:
                    partition_cols.append("year")
                if "month" in df.columns and (month is not None or year is not None):
                    partition_cols.append("month")
                
                if partition_cols:
                    if order_direction.lower() == "desc":
                        window = Window.partitionBy(*partition_cols).orderBy(F.col(order_column).desc())
                    else:
                        window = Window.partitionBy(*partition_cols).orderBy(F.col(order_column).asc())
                else:
                    logger.warning("No partition columns available for window function - performance may be degraded")
                    if order_direction.lower() == "desc":
                        window = Window.orderBy(F.col(order_column).desc())
                    else:
                        window = Window.orderBy(F.col(order_column).asc())
                
                if order_direction.lower() == "desc":
                    df = df.orderBy(F.col(order_column).desc())
                else:
                    df = df.orderBy(F.col(order_column).asc())
                
                df = df.withColumn("_row_num", F.row_number().over(window))
                
                page_df = df.filter(
                    (F.col("_row_num") > offset) & 
                    (F.col("_row_num") <= offset + page_size)
                ).drop("_row_num")
            
            essential_columns = [
                "VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
                "passenger_count", "trip_distance", "fare_amount", "tip_amount",
                "total_amount", "payment_type", "trip_duration_minutes"
            ]
            available_columns = [col for col in essential_columns if col in page_df.columns]
            page_df = page_df.select(available_columns)
            
            page_data = page_df.limit(page_size).toPandas()
            
            records = page_data.to_dict(orient="records")
            
            for record in records:
                for key, value in record.items():
                    if hasattr(value, 'item'):
                        record[key] = value.item()
                    elif hasattr(value, 'tolist'):
                        record[key] = value.tolist()
                    elif value is None:
                        record[key] = None
            
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
        try:
            import os
            F = get_spark_functions()
            
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
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.data_path)
            
            if year:
                df = df.filter(F.year("tpep_pickup_datetime") == year)
            if month:
                df = df.filter(F.month("tpep_pickup_datetime") == month)
            
            stats_row = df.agg(
                F.min(field).alias("min_val"),
                F.max(field).alias("max_val")
            ).collect()[0]
            
            stats = stats_row.asDict()
            min_val = float(stats["min_val"]) if stats["min_val"] is not None else 0.0
            max_val = float(stats["max_val"]) if stats["max_val"] is not None else 1.0
            
            bin_width = (max_val - min_val) / bins if max_val > min_val else 1.0
            
            df_with_bins = df.withColumn(
                "bin",
                F.floor((F.col(field) - min_val) / bin_width).cast("int")
            ).filter(F.col("bin") >= 0).filter(F.col("bin") < bins)
            
            histogram_rows = df_with_bins.groupBy("bin").count().orderBy("bin").collect()
            
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
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.data_path)
            
            if year:
                df = df.filter(F.year("tpep_pickup_datetime") == year)
            if month:
                df = df.filter(F.month("tpep_pickup_datetime") == month)
            
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

