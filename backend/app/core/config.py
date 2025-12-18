from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NYC Taxi Data Analysis API"
    VERSION: str = "1.0.0"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8000",
    ]
    
    DATA_DIR: str = os.getenv("DATA_DIR", "../data")
    PROCESSED_DATA_DIR: str = os.path.join(DATA_DIR, "processed")
    OUTPUT_DATA_DIR: str = os.path.join(DATA_DIR, "output")
    MODELS_DIR: str = os.getenv("MODELS_DIR", "../models")
    
    _base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    PROCESSED_DATA_DIR_ABS: str = os.path.join(_base_dir, "data", "processed")
    OUTPUT_DATA_DIR_ABS: str = os.path.join(_base_dir, "data", "output")
    MODELS_DIR_ABS: str = os.path.join(_base_dir, "models")
    
    SPARK_MASTER: str = os.getenv("SPARK_MASTER", "local[*]")
    SPARK_APP_NAME: str = "NYC_Taxi_API"
    
    CACHE_TTL: int = 3600
    ENABLE_CACHE: bool = True
    
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

