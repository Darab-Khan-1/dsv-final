"""
Response Schemas
Pydantic models for API responses
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    service: str


class SparkHealthResponse(BaseModel):
    """Spark health check response"""
    status: str
    spark_version: Optional[str] = None
    spark_master: Optional[str] = None
    timestamp: str
    error: Optional[str] = None


class TripCountResponse(BaseModel):
    """Trip count response"""
    data: List[Dict[str, Any]]


class PeakHoursResponse(BaseModel):
    """Peak hours response"""
    data: List[Dict[str, int]]


class DurationDistributionResponse(BaseModel):
    """Duration distribution response"""
    mean: float
    stddev: float
    min: float
    max: float
    median: float
    p25: float
    p75: float


class HotspotResponse(BaseModel):
    """Hotspot response"""
    data: List[Dict[str, Any]]


class CorrelationResponse(BaseModel):
    """Correlation response"""
    columns: List[str]
    correlation_matrix: List[List[float]]


class MarketShareResponse(BaseModel):
    """Market share response"""
    data: List[Dict[str, Any]]


class FarePredictionResponse(BaseModel):
    """Fare prediction response"""
    predicted_fare: Optional[float] = None
    input: Dict[str, Any]
    error: Optional[str] = None
    message: Optional[str] = None

