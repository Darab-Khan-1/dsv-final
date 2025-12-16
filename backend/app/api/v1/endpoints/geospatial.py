"""
Geospatial Analysis Endpoints
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.geospatial_service import GeospatialAnalysisService

router = APIRouter()
service = GeospatialAnalysisService()


@router.get("/pickup-hotspots")
async def get_pickup_hotspots(
    top_n: int = Query(20, description="Number of hotspots to return"),
    min_trips: int = Query(100, description="Minimum trips threshold")
):
    """Get top pickup hotspots"""
    try:
        result = await service.get_pickup_hotspots(top_n, min_trips)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dropoff-hotspots")
async def get_dropoff_hotspots(
    top_n: int = Query(20, description="Number of hotspots to return"),
    min_trips: int = Query(100, description="Minimum trips threshold")
):
    """Get top dropoff hotspots"""
    try:
        result = await service.get_dropoff_hotspots(top_n, min_trips)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/route-pairs")
async def get_route_pairs(
    top_n: int = Query(20, description="Number of route pairs to return")
):
    """Get most common route pairs (pickup → dropoff)"""
    try:
        result = await service.get_route_pairs(top_n)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/zone-comparison")
async def get_zone_comparison(
    zone_type: str = Query("airport", description="Zone type: airport, inner_city, suburban")
):
    """Compare trip characteristics by zone type"""
    try:
        result = await service.get_zone_comparison(zone_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters")
async def get_clusters(
    n_clusters: int = Query(20, description="Number of clusters"),
    cluster_type: str = Query("kmeans", description="Cluster type: kmeans, dbscan")
):
    """Get geospatial clusters"""
    try:
        result = await service.get_clusters(n_clusters, cluster_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/spatial-density")
async def get_spatial_density(
    grid_size: float = Query(0.01, description="Grid size in degrees")
):
    """Get spatial density heatmap data"""
    try:
        result = await service.get_spatial_density(grid_size)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

