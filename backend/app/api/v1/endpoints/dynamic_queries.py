from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

from src.config import DATA_DIR


router = APIRouter()


def _get_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("TaxiAPI-Dynamic")
        .config("spark.executor.memory", "2g")
        .config("spark.driver.memory", "1g")
        .getOrCreate()
    )


@router.get("/temporal/hourly")
async def get_hourly_temporal(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    day_of_week: Optional[List[int]] = Query(None),
    hour: Optional[int] = Query(None, ge=0, le=23),
):
    try:
        spark = _get_spark()
        df = spark.read.parquet(
            str(DATA_DIR / "aggregates" / "temporal_hourly_stats.parquet")
        )

        if year is not None:
            df = df.filter(col("pickup_year") == int(year))
        if month is not None:
            df = df.filter(col("pickup_month") == int(month))
        if day_of_week:
            df = df.filter(col("pickup_day_of_week").isin(day_of_week))
        if hour is not None:
            df = df.filter(col("pickup_hour") == int(hour))

        result = df.toPandas().to_dict("records")
        return {
            "status": "success",
            "row_count": len(result),
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/geospatial/zones")
async def get_zone_stats(
    year: int = Query(...),
    month: int = Query(...),
    hour_bucket: Optional[str] = Query(
        None, regex="^(morning|afternoon|evening|night)$"
    ),
    min_trips: int = Query(10, ge=1),
):
    try:
        spark = _get_spark()
        df = spark.read.parquet(
            str(DATA_DIR / "aggregates" / "geospatial_zone_stats.parquet")
        )

        df = df.filter(
            (col("pickup_year") == int(year)) & (col("pickup_month") == int(month))
        )

        if hour_bucket:
            df = df.filter(col("hour_bucket") == hour_bucket)

        df = df.filter(col("trip_count") >= int(min_trips))

        result = df.toPandas().to_dict("records")
        return {
            "status": "success",
            "row_count": len(result),
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


