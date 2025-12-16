"""
Data Endpoints
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.data_service import DataService

router = APIRouter()
service = DataService()


@router.get("/summary")
async def get_data_summary():
    """Get dataset summary statistics"""
    try:
        result = await service.get_data_summary()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sample")
async def get_data_sample(
    n: int = Query(100, description="Number of records"),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None)
):
    """Get sample data"""
    try:
        result = await service.get_data_sample(n, year, month)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/date-range")
async def get_date_range():
    """Get available date range in dataset"""
    try:
        result = await service.get_date_range()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/distribution")
async def get_distribution(
    field: str = Query(..., description="Field name (e.g., fare_amount, trip_distance)"),
    bins: int = Query(20, description="Number of bins"),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None)
):
    """Get distribution histogram data for a field"""
    try:
        result = await service.get_distribution(field, bins, year, month)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scatter")
async def get_scatter_data(
    x_field: str = Query(..., description="X-axis field name"),
    y_field: str = Query(..., description="Y-axis field name"),
    sample_size: int = Query(1000, description="Sample size for scatter plot"),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None)
):
    """Get scatter plot data (sampled for performance)"""
    try:
        result = await service.get_scatter_data(x_field, y_field, sample_size, year, month)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paginated")
async def get_paginated_data(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of records per page"),
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month"),
    payment_type: Optional[int] = Query(None, description="Filter by payment type (1=Card, 2=Cash)"),
    min_fare: Optional[float] = Query(None, description="Minimum fare amount"),
    max_fare: Optional[float] = Query(None, description="Maximum fare amount"),
    min_distance: Optional[float] = Query(None, description="Minimum trip distance (miles)"),
    max_distance: Optional[float] = Query(None, description="Maximum trip distance (miles)"),
    min_passengers: Optional[int] = Query(None, ge=1, description="Minimum passenger count"),
    max_passengers: Optional[int] = Query(None, ge=1, description="Maximum passenger count"),
    order_by: Optional[str] = Query(None, description="Column to order by"),
    order_direction: str = Query("asc", regex="^(asc|desc)$", description="Order direction")
):
    """Get paginated data using Spark SQL with multiple filters"""
    try:
        result = await service.get_paginated_data(
            page=page,
            page_size=page_size,
            year=year,
            month=month,
            payment_type=payment_type,
            min_fare=min_fare,
            max_fare=max_fare,
            min_distance=min_distance,
            max_distance=max_distance,
            min_passengers=min_passengers,
            max_passengers=max_passengers,
            order_by=order_by,
            order_direction=order_direction
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

