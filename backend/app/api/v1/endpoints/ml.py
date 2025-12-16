"""
Machine Learning Endpoints
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.ml_service import MLService

router = APIRouter()
service = MLService()


@router.post("/predict-fare")
async def predict_fare(
    pickup_datetime: str,
    pickup_latitude: float,
    pickup_longitude: float,
    dropoff_latitude: float,
    dropoff_longitude: float,
    passenger_count: int,
    trip_distance: Optional[float] = None
):
    """Predict taxi fare using trained model"""
    try:
        result = await service.predict_fare(
            pickup_datetime,
            pickup_latitude,
            pickup_longitude,
            dropoff_latitude,
            dropoff_longitude,
            passenger_count,
            trip_distance
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-info")
async def get_model_info():
    """Get information about trained models"""
    try:
        result = await service.get_model_info()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-importance")
async def get_feature_importance(
    model_name: str = Query("random_forest", description="Model name")
):
    """Get feature importance from trained model"""
    try:
        result = await service.get_feature_importance(model_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-metrics")
async def get_model_metrics(
    model_name: str = Query("random_forest", description="Model name (random_forest, gbt, linear_regression)")
):
    """Get model metrics (R², RMSE, training samples)"""
    try:
        result = await service.get_model_metrics(model_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

