from fastapi import APIRouter
from datetime import datetime
from app.core.spark_session import get_spark_session

router = APIRouter()


@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "nyc-taxi-api"
    }


@router.get("/spark")
async def spark_health():
    try:
        spark = get_spark_session()
        return {
            "status": "healthy",
            "spark_version": spark.version,
            "spark_master": spark.sparkContext.master,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

