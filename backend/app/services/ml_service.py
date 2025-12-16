"""
Machine Learning Service
Business logic for ML endpoints
"""

from typing import Dict, Any, Optional
import os
import logging
from app.core.spark_session import get_spark_session
from app.core.config import settings
from app.utils.spark_imports import get_spark_ml, get_spark_types

logger = logging.getLogger(__name__)


class MLService:
    """Service for machine learning operations"""
    
    def __init__(self):
        self._spark = None
        # Use absolute path - backend/app/services -> backend -> project_root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.models_dir = os.path.join(base_dir, "..", "models")
        self.models = {}
    
    @property
    def spark(self):
        """Lazy Spark session property"""
        if self._spark is None:
            self._spark = get_spark_session()
        return self._spark
    
    def _load_model(self, model_name: str):
        """Load a trained model"""
        model_path = os.path.join(self.models_dir, model_name)
        if not os.path.exists(model_path):
            return None
        
        try:
            ml_modules = get_spark_ml()
            RandomForestRegressionModel = ml_modules["RandomForestRegressionModel"]
            GBTRegressionModel = ml_modules["GBTRegressionModel"]
            LinearRegressionModel = ml_modules["LinearRegressionModel"]
            
            # Try different model types
            if "random_forest" in model_name.lower():
                return RandomForestRegressionModel.load(model_path)
            elif "gbt" in model_name.lower() or "gradient" in model_name.lower():
                return GBTRegressionModel.load(model_path)
            elif "linear" in model_name.lower():
                return LinearRegressionModel.load(model_path)
            else:
                # Default to random forest
                return RandomForestRegressionModel.load(model_path)
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return None
    
    async def predict_fare(
        self,
        pickup_datetime: str,
        pickup_latitude: float,
        pickup_longitude: float,
        dropoff_latitude: float,
        dropoff_longitude: float,
        passenger_count: int,
        trip_distance: Optional[float] = None
    ) -> Dict[str, Any]:
        """Predict taxi fare"""
        try:
            from pyspark.sql import Row
            from datetime import datetime
            import math
            
            ml_modules = get_spark_ml()
            types = get_spark_types()
            VectorAssembler = ml_modules["VectorAssembler"]
            StructType = types["StructType"]
            StructField = types["StructField"]
            DoubleType = types["DoubleType"]
            IntegerType = types["IntegerType"]
            
            # Check if model exists
            model_name = "fare_prediction_model"
            model = self._load_model(model_name)
            
            if model is None:
                return {
                    "error": "Model not found. Please train the model first.",
                    "message": "Run the ML training pipeline to create a model."
                }
            
            # Parse datetime
            pickup_dt = datetime.strptime(pickup_datetime, "%Y-%m-%d %H:%M:%S")
            
            # Calculate Haversine distance if not provided
            if trip_distance is None:
                R = 3959  # Earth radius in miles
                lat1, lon1 = math.radians(pickup_latitude), math.radians(pickup_longitude)
                lat2, lon2 = math.radians(dropoff_latitude), math.radians(dropoff_longitude)
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                c = 2 * math.asin(math.sqrt(a))
                trip_distance = R * c
            
            # Create feature vector
            features = [
                pickup_latitude,
                pickup_longitude,
                dropoff_latitude,
                dropoff_longitude,
                passenger_count,
                trip_distance,
                pickup_dt.hour,
                pickup_dt.weekday() + 1,  # dayofweek
                pickup_dt.month,
                pickup_dt.year
            ]
            
            # Create DataFrame
            schema = StructType([
                StructField("pickup_latitude", DoubleType()),
                StructField("pickup_longitude", DoubleType()),
                StructField("dropoff_latitude", DoubleType()),
                StructField("dropoff_longitude", DoubleType()),
                StructField("passenger_count", IntegerType()),
                StructField("trip_distance", DoubleType()),
                StructField("hour", IntegerType()),
                StructField("day_of_week", IntegerType()),
                StructField("month", IntegerType()),
                StructField("year", IntegerType()),
            ])
            
            df = self.spark.createDataFrame([Row(*features)], schema)
            
            # Assemble features
            assembler = VectorAssembler(
                inputCols=schema.fieldNames(),
                outputCol="features"
            )
            df_features = assembler.transform(df)
            
            # Make prediction
            prediction = model.transform(df_features)
            predicted_fare = prediction.select("prediction").collect()[0][0]
            
            return {
                "predicted_fare": float(predicted_fare),
                "input": {
                    "pickup_datetime": pickup_datetime,
                    "pickup_latitude": pickup_latitude,
                    "pickup_longitude": pickup_longitude,
                    "dropoff_latitude": dropoff_latitude,
                    "dropoff_longitude": dropoff_longitude,
                    "passenger_count": passenger_count,
                    "trip_distance": trip_distance
                }
            }
        except Exception as e:
            logger.error(f"Error in predict_fare: {e}")
            return {
                "error": str(e),
                "message": "Error making prediction"
            }
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        try:
            models = []
            
            if os.path.exists(self.models_dir):
                for item in os.listdir(self.models_dir):
                    model_path = os.path.join(self.models_dir, item)
                    if os.path.isdir(model_path):
                        models.append({
                            "name": item,
                            "path": model_path,
                            "exists": True
                        })
            
            return {
                "models": models,
                "models_directory": self.models_dir,
                "message": f"Found {len(models)} model(s)" if models else "No models found. Train a model first."
            }
        except Exception as e:
            logger.error(f"Error in get_model_info: {e}")
            raise
    
    async def get_model_metrics(self, model_name: str = "random_forest") -> Dict[str, Any]:
        """Get model metrics (R², RMSE, training samples)"""
        try:
            import json
            
            metrics_path = os.path.join(self.models_dir, "model_metrics.json")
            
            if not os.path.exists(metrics_path):
                return {
                    "error": "Model metrics not found",
                    "message": "Please train a model first to generate metrics."
                }
            
            with open(metrics_path, 'r') as f:
                metrics_data = json.load(f)
            
            # Map model names to keys in metrics file
            model_key_map = {
                "random_forest": "random_forest",
                "rf": "random_forest",
                "gbt": "gbt",
                "gradient_boosted": "gbt",
                "linear_regression": "linear_regression",
                "lr": "linear_regression"
            }
            
            key = model_key_map.get(model_name.lower(), "random_forest")
            
            if key not in metrics_data:
                # Try to find any available model
                available_models = list(metrics_data.keys())
                if available_models:
                    key = available_models[0]
                    logger.warning(f"Model {model_name} not found, using {key}")
                else:
                    return {
                        "error": f"Model {model_name} metrics not found",
                        "message": "No model metrics available."
                    }
            
            model_metrics = metrics_data[key]
            
            # Format training samples for display
            training_samples = model_metrics.get("training_samples", 0)
            if training_samples >= 1_000_000:
                training_samples_display = f"{(training_samples / 1_000_000):.1f}M"
            elif training_samples >= 1_000:
                training_samples_display = f"{(training_samples / 1_000):.1f}K"
            else:
                training_samples_display = str(training_samples)
            
            # Get feature importance if available
            feature_importance = model_metrics.get("feature_importance")
            if feature_importance and isinstance(feature_importance, dict):
                # Already in dict format from JSON
                pass
            elif feature_importance and isinstance(feature_importance, list):
                # Convert from list of tuples to dict
                feature_importance = {feature: importance for feature, importance in feature_importance}
            else:
                feature_importance = None
            
            return {
                "model_type": model_metrics.get("model_type", "Unknown"),
                "r2": model_metrics.get("r2", 0.0),
                "rmse": model_metrics.get("rmse", 0.0),
                "mae": model_metrics.get("mae", 0.0),
                "training_samples": training_samples,
                "training_samples_display": training_samples_display,
                "feature_importance": feature_importance
            }
        except Exception as e:
            logger.error(f"Error in get_model_metrics: {e}")
            return {
                "error": str(e),
                "message": "Error reading model metrics"
            }
    
    async def get_feature_importance(self, model_name: str) -> Dict[str, Any]:
        """Get feature importance"""
        try:
            model = self._load_model(model_name)
            
            if model is None:
                return {
                    "error": f"Model {model_name} not found",
                    "message": "Please train the model first."
                }
            
            # Get feature importance if available
            if hasattr(model, "featureImportances"):
                importances = model.featureImportances.toArray().tolist()
                feature_names = [
                    "pickup_latitude", "pickup_longitude",
                    "dropoff_latitude", "dropoff_longitude",
                    "passenger_count", "trip_distance",
                    "hour", "day_of_week", "month", "year"
                ]
                
                return {
                    "model_name": model_name,
                    "feature_importance": [
                        {"feature": name, "importance": imp}
                        for name, imp in zip(feature_names, importances)
                    ]
                }
            else:
                return {
                    "model_name": model_name,
                    "message": "Feature importance not available for this model type"
                }
        except Exception as e:
            logger.error(f"Error in get_feature_importance: {e}")
            raise

