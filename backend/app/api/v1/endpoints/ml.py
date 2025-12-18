from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from pydantic import BaseModel

from app.services.ml_service import MLService

router = APIRouter()
service = MLService()


class FarePredictionRequest(BaseModel):
    pickup_datetime: str
    pickup_latitude: float
    pickup_longitude: float
    dropoff_latitude: float
    dropoff_longitude: float
    passenger_count: int
    trip_distance: Optional[float] = None


@router.post("/predict-fare")
async def predict_fare(payload: FarePredictionRequest):
    try:
        result = await service.predict_fare(
            payload.pickup_datetime,
            payload.pickup_latitude,
            payload.pickup_longitude,
            payload.dropoff_latitude,
            payload.dropoff_longitude,
            payload.passenger_count,
            payload.trip_distance,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-info")
async def get_model_info():
    try:
        result = await service.get_model_info()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-importance")
async def get_feature_importance(
    model_name: str = Query("random_forest", description="Model name")
):
    try:
        result = await service.get_feature_importance(model_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-metrics")
async def get_model_metrics(
    model_name: str = Query("random_forest", description="Model name (random_forest, gbt, linear_regression)")
):
    try:
        result = await service.get_model_metrics(model_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

