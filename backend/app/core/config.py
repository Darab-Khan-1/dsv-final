"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NYC Taxi Data Analysis API"
    VERSION: str = "1.0.0"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
        "http://localhost:8080",  # Vite custom port (this project)
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8000",
    ]
    
    # Data Paths (relative to backend directory)
    DATA_DIR: str = os.getenv("DATA_DIR", "../data")
    PROCESSED_DATA_DIR: str = os.path.join(DATA_DIR, "processed")
    OUTPUT_DATA_DIR: str = os.path.join(DATA_DIR, "output")
    MODELS_DIR: str = os.getenv("MODELS_DIR", "../models")
    
    # Resolve absolute paths
    _base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    PROCESSED_DATA_DIR_ABS: str = os.path.join(_base_dir, "data", "processed")
    OUTPUT_DATA_DIR_ABS: str = os.path.join(_base_dir, "data", "output")
    MODELS_DIR_ABS: str = os.path.join(_base_dir, "models")
    
    # Spark Settings
    SPARK_MASTER: str = os.getenv("SPARK_MASTER", "local[*]")
    SPARK_APP_NAME: str = "NYC_Taxi_API"
    
    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour in seconds
    ENABLE_CACHE: bool = True
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

