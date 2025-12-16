"""
API v1 Router
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    temporal,
    geospatial,
    economic,
    ml,
    data,
    dynamic_queries,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(temporal.router, prefix="/temporal", tags=["temporal"])
api_router.include_router(geospatial.router, prefix="/geospatial", tags=["geospatial"])
api_router.include_router(economic.router, prefix="/economic", tags=["economic"])
api_router.include_router(ml.router, prefix="/ml", tags=["machine-learning"])
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(
    dynamic_queries.router, prefix="/dynamic", tags=["dynamic-aggregates"]
)

