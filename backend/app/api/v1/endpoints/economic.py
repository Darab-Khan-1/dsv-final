from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.economic_service import EconomicAnalysisService

router = APIRouter()
service = EconomicAnalysisService()


@router.get("/correlations")
async def get_correlations():
    try:
        result = await service.get_correlations()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tip-analysis")
async def get_tip_analysis(
    group_by: str = Query("payment_type", description="Group by: payment_type, hour, distance_bucket, location")
):
    try:
        result = await service.get_tip_analysis(group_by)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue-analysis")
async def get_revenue_analysis(
    group_by: str = Query("hour", description="Group by: hour, location, zone"),
    year: Optional[int] = Query(None)
):
    try:
        result = await service.get_revenue_analysis(group_by, year)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/price-elasticity")
async def get_price_elasticity():
    try:
        result = await service.get_price_elasticity()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/surge-pricing")
async def get_surge_pricing(
    threshold: float = Query(3.0, description="Z-score threshold for surge detection")
):
    try:
        result = await service.get_surge_pricing(threshold)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer-segments")
async def get_customer_segments(
    n_segments: int = Query(5, description="Number of customer segments")
):
    try:
        result = await service.get_customer_segments(n_segments)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-share")
async def get_market_share():
    try:
        result = await service.get_market_share()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights")
async def get_economic_insights():
    try:
        result = await service.get_economic_insights()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

