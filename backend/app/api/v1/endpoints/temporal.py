from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
from app.services.temporal_service import TemporalAnalysisService

router = APIRouter()
service = TemporalAnalysisService()


@router.get("/trips-by-hour")
async def get_trips_by_hour(
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, description="Filter by month"),
    day_of_week: Optional[int] = Query(None, description="Filter by day of week (1-7)")
):
    try:
        result = await service.get_trips_by_hour(year, month, day_of_week)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trips-by-day")
async def get_trips_by_day(
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, description="Filter by month")
):
    try:
        result = await service.get_trips_by_day(year, month)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trips-by-month")
async def get_trips_by_month(
    year: Optional[int] = Query(None, description="Filter by year")
):
    try:
        result = await service.get_trips_by_month(year)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/peak-hours")
async def get_peak_hours(
    top_n: int = Query(10, description="Number of top hours to return")
):
    try:
        result = await service.get_peak_hours(top_n)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/duration-distribution")
async def get_duration_distribution(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None)
):
    try:
        result = await service.get_duration_distribution(year, month)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fare-trends")
async def get_fare_trends(
    group_by: str = Query("month", description="Group by: hour, day, month"),
    year: Optional[int] = Query(None)
):
    try:
        result = await service.get_fare_trends(group_by, year)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/time-series-decomposition")
async def get_time_series_decomposition(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    try:
        result = await service.get_time_series_decomposition(start_date, end_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

