"""
Stage 5: Machine Learning - Fare Prediction
Train ML models to predict taxi fares
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    hour,
    dayofweek,
    month,
    year,
    when,
    isnan,
    isnull,
    abs as spark_abs,
)
from pyspark.ml import Pipeline
from pyspark.ml.feature import (
    VectorAssembler, StandardScaler, StringIndexer
)
from pyspark.ml.regression import (
    RandomForestRegressor, GBTRegressor, LinearRegression
)
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
import logging

from src.config import PROCESSED_DATA_DIR, MODELS_DIR

logger = logging.getLogger(__name__)


class MLModelTrainer:
    """Train ML models for fare prediction"""
    
    def __init__(self, spark: SparkSession, data_path: Path = None):
        self.spark = spark
        if data_path is None:
            data_path = PROCESSED_DATA_DIR / "cleaned_data.parquet"
        self.data_path = data_path
        self.models_dir = MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.df = None
        self.training_df = None
        self.test_df = None
    
    def _load_data(self):
        """Load and prepare data"""
        if self.df is None:
            logger.info(f"Loading data from {self.data_path}")
            self.df = self.spark.read.parquet(str(self.data_path))
            logger.info(f"Loaded {self.df.count():,} records")
        return self.df
    
    def _prepare_features(self, df):
        """Prepare features for ML model"""
        logger.info("Preparing features...")
        
        # Extract temporal features (ensure they exist even if cleaning changed)
        df_features = (
            df.withColumn("pickup_hour", hour("tpep_pickup_datetime"))
            .withColumn("pickup_day_of_week", dayofweek("tpep_pickup_datetime"))
            .withColumn("pickup_month", month("tpep_pickup_datetime"))
            .withColumn("pickup_year", year("tpep_pickup_datetime"))
        )
        
        # Calculate Haversine distance if not present
        # (assuming trip_distance is already calculated, but we can add it as a feature)
        
        # Select features for model
        feature_cols = [
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
            "passenger_count",
            "trip_distance",
            "pickup_hour",
            "pickup_day_of_week",
            "pickup_month",
            "pickup_year"
        ]
        
        # Filter out nulls and invalid values
        df_clean = df_features.select(feature_cols + ["fare_amount"]) \
            .filter(
                col("fare_amount").isNotNull() &
                (col("fare_amount") > 0) &
                col("trip_distance").isNotNull() &
                (col("trip_distance") > 0) &
                col("pickup_latitude").isNotNull() &
                col("pickup_longitude").isNotNull() &
                col("dropoff_latitude").isNotNull() &
                col("dropoff_longitude").isNotNull()
            )
        
        logger.info(f"Prepared {df_clean.count():,} records with features")
        return df_clean, feature_cols
    
    def _split_data(self, df, train_ratio=0.8, test_ratio=0.2):
        """Split data into training and test sets"""
        logger.info(f"Splitting data: {train_ratio*100:.0f}% train, {test_ratio*100:.0f}% test")
        
        # Sample for faster training; cap to avoid driver/executor OOM
        df_sample = (
            df.sample(0.15, seed=42)  # 15% sample
              .limit(300_000)         # hard cap rows to bound memory
        )
        logger.info(f"Using sample of {df_sample.count():,} records for training")
        
        # Repartition sample for better memory distribution (avoid shuffle)
        df_sample = df_sample.coalesce(80)
        
        train_df, test_df = df_sample.randomSplit([train_ratio, test_ratio], seed=42)
        logger.info(f"Training set: {train_df.count():,} records")
        logger.info(f"Test set: {test_df.count():,} records")
        
        return train_df, test_df
    
    def train_random_forest(self, 
                           num_trees: int = 100,
                           max_depth: int = 10,
                           save_model: bool = True) -> Dict[str, Any]:
        """Train Random Forest model"""
        logger.info("=" * 60)
        logger.info("Training Random Forest Model")
        logger.info("=" * 60)
        
        df = self._load_data()
        df_features, feature_cols = self._prepare_features(df)
        
        if self.training_df is None or self.test_df is None:
            self.training_df, self.test_df = self._split_data(df_features)
        
        # Create feature vector
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features"
        )
        
        # Scale features
        scaler = StandardScaler(
            inputCol="features",
            outputCol="scaled_features",
            withStd=True,
            withMean=True
        )
        
        # Random Forest model
        rf = RandomForestRegressor(
            featuresCol="scaled_features",
            labelCol="fare_amount",
            numTrees=num_trees,
            maxDepth=max_depth,
            seed=42
        )
        
        # Create pipeline
        pipeline = Pipeline(stages=[assembler, scaler, rf])
        
        # Train model
        logger.info("Training model...")
        model = pipeline.fit(self.training_df)
        
        # Make predictions
        logger.info("Making predictions...")
        predictions = model.transform(self.test_df)
        
        # Evaluate model
        evaluator = RegressionEvaluator(
            labelCol="fare_amount",
            predictionCol="prediction",
            metricName="rmse"
        )
        
        rmse = evaluator.evaluate(predictions)
        mae = evaluator.setMetricName("mae").evaluate(predictions)
        r2 = evaluator.setMetricName("r2").evaluate(predictions)
        
        logger.info(f"Model Performance:")
        logger.info(f"  RMSE: ${rmse:.2f}")
        logger.info(f"  MAE: ${mae:.2f}")
        logger.info(f"  R²: {r2:.4f}")
        
        # Save model
        if save_model:
            model_path = self.models_dir / "fare_prediction_rf_model"
            model.write().overwrite().save(str(model_path))
            logger.info(f"Model saved to {model_path}")
        
        # Get feature importance
        rf_model = model.stages[-1]
        feature_importance = list(zip(feature_cols, rf_model.featureImportances.toArray()))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        # Get training samples count
        training_samples = self.training_df.count()
        
        results = {
            "model_type": "RandomForest",
            "rmse": float(rmse),
            "mae": float(mae),
            "r2": float(r2),
            "training_samples": int(training_samples),
            "feature_importance": feature_importance,
            "model_path": str(model_path) if save_model else None
        }
        
        # Save metrics to JSON file
        if save_model:
            metrics_path = self.models_dir / "model_metrics.json"
            # Convert feature_importance from list of tuples to dict for JSON serialization
            feature_importance_dict = {feature: float(importance) for feature, importance in feature_importance}
            
            metrics_data = {
                "random_forest": {
                    "model_type": "RandomForest",
                    "r2": float(r2),
                    "rmse": float(rmse),
                    "mae": float(mae),
                    "training_samples": int(training_samples),
                    "feature_importance": feature_importance_dict
                }
            }
            # Read existing metrics if file exists
            if metrics_path.exists():
                try:
                    with open(metrics_path, 'r') as f:
                        existing_metrics = json.load(f)
                    existing_metrics.update(metrics_data)
                    metrics_data = existing_metrics
                except Exception as e:
                    logger.warning(f"Could not read existing metrics file: {e}")
            
            with open(metrics_path, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            logger.info(f"Model metrics saved to {metrics_path}")
        
        return results
    
    def train_gbt(self, 
                 max_iter: int = 100,
                 max_depth: int = 5,
                 save_model: bool = True) -> Dict[str, Any]:
        """Train Gradient Boosted Tree model"""
        logger.info("=" * 60)
        logger.info("Training Gradient Boosted Tree Model")
        logger.info("=" * 60)
        
        df = self._load_data()
        df_features, feature_cols = self._prepare_features(df)
        
        if self.training_df is None or self.test_df is None:
            self.training_df, self.test_df = self._split_data(df_features)
        
        # Create feature vector
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features"
        )
        
        # Scale features
        scaler = StandardScaler(
            inputCol="features",
            outputCol="scaled_features",
            withStd=True,
            withMean=True
        )
        
        # GBT model
        gbt = GBTRegressor(
            featuresCol="scaled_features",
            labelCol="fare_amount",
            maxIter=max_iter,
            maxDepth=max_depth,
            seed=42
        )
        
        # Create pipeline
        pipeline = Pipeline(stages=[assembler, scaler, gbt])
        
        # Train model
        logger.info("Training model...")
        model = pipeline.fit(self.training_df)
        
        # Make predictions
        logger.info("Making predictions...")
        predictions = model.transform(self.test_df)
        
        # Evaluate model
        evaluator = RegressionEvaluator(
            labelCol="fare_amount",
            predictionCol="prediction",
            metricName="rmse"
        )
        
        rmse = evaluator.evaluate(predictions)
        mae = evaluator.setMetricName("mae").evaluate(predictions)
        r2 = evaluator.setMetricName("r2").evaluate(predictions)
        
        logger.info(f"Model Performance:")
        logger.info(f"  RMSE: ${rmse:.2f}")
        logger.info(f"  MAE: ${mae:.2f}")
        logger.info(f"  R²: {r2:.4f}")
        
        # Save model
        if save_model:
            model_path = self.models_dir / "fare_prediction_gbt_model"
            model.write().overwrite().save(str(model_path))
            logger.info(f"Model saved to {model_path}")
        
        # Get feature importance
        gbt_model = model.stages[-1]
        feature_importance = list(zip(feature_cols, gbt_model.featureImportances.toArray()))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        # Get training samples count
        training_samples = self.training_df.count()
        
        results = {
            "model_type": "GBT",
            "rmse": float(rmse),
            "mae": float(mae),
            "r2": float(r2),
            "training_samples": int(training_samples),
            "feature_importance": feature_importance,
            "model_path": str(model_path) if save_model else None
        }
        
        # Save metrics to JSON file
        if save_model:
            metrics_path = self.models_dir / "model_metrics.json"
            # Convert feature_importance from list of tuples to dict for JSON serialization
            feature_importance_dict = {feature: float(importance) for feature, importance in feature_importance}
            
            metrics_data = {
                "gbt": {
                    "model_type": "GBT",
                    "r2": float(r2),
                    "rmse": float(rmse),
                    "mae": float(mae),
                    "training_samples": int(training_samples),
                    "feature_importance": feature_importance_dict
                }
            }
            # Read existing metrics if file exists
            if metrics_path.exists():
                try:
                    with open(metrics_path, 'r') as f:
                        existing_metrics = json.load(f)
                    existing_metrics.update(metrics_data)
                    metrics_data = existing_metrics
                except Exception as e:
                    logger.warning(f"Could not read existing metrics file: {e}")
            
            with open(metrics_path, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            logger.info(f"Model metrics saved to {metrics_path}")
        
        return results
    
    def train_linear_regression(self, save_model: bool = True) -> Dict[str, Any]:
        """Train Linear Regression model"""
        logger.info("=" * 60)
        logger.info("Training Linear Regression Model")
        logger.info("=" * 60)
        
        df = self._load_data()
        df_features, feature_cols = self._prepare_features(df)
        
        if self.training_df is None or self.test_df is None:
            self.training_df, self.test_df = self._split_data(df_features)
        
        # Create feature vector
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features"
        )
        
        # Scale features
        scaler = StandardScaler(
            inputCol="features",
            outputCol="scaled_features",
            withStd=True,
            withMean=True
        )
        
        # Linear Regression model
        lr = LinearRegression(
            featuresCol="scaled_features",
            labelCol="fare_amount",
            maxIter=100,
            regParam=0.01
        )
        
        # Create pipeline
        pipeline = Pipeline(stages=[assembler, scaler, lr])
        
        # Train model
        logger.info("Training model...")
        model = pipeline.fit(self.training_df)
        
        # Make predictions
        logger.info("Making predictions...")
        predictions = model.transform(self.test_df)
        
        # Evaluate model
        evaluator = RegressionEvaluator(
            labelCol="fare_amount",
            predictionCol="prediction",
            metricName="rmse"
        )
        
        rmse = evaluator.evaluate(predictions)
        mae = evaluator.setMetricName("mae").evaluate(predictions)
        r2 = evaluator.setMetricName("r2").evaluate(predictions)
        
        logger.info(f"Model Performance:")
        logger.info(f"  RMSE: ${rmse:.2f}")
        logger.info(f"  MAE: ${mae:.2f}")
        logger.info(f"  R²: {r2:.4f}")
        
        # Save model
        if save_model:
            model_path = self.models_dir / "fare_prediction_lr_model"
            model.write().overwrite().save(str(model_path))
            logger.info(f"Model saved to {model_path}")
        
        lr_model = model.stages[-1]
        coefficients = list(zip(feature_cols, lr_model.coefficients.toArray()))
        
        # Convert coefficients to feature importance (use absolute values and normalize)
        coeff_abs = [abs(coeff) for _, coeff in coefficients]
        total_abs = sum(coeff_abs) if coeff_abs else 1.0
        feature_importance = [(feature, abs(coeff) / total_abs) for feature, coeff in coefficients]
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        # Get training samples count
        training_samples = self.training_df.count()
        
        results = {
            "model_type": "LinearRegression",
            "rmse": float(rmse),
            "mae": float(mae),
            "r2": float(r2),
            "training_samples": int(training_samples),
            "coefficients": coefficients,
            "feature_importance": feature_importance,
            "model_path": str(model_path) if save_model else None
        }
        
        # Save metrics to JSON file
        if save_model:
            metrics_path = self.models_dir / "model_metrics.json"
            # Convert feature_importance from list of tuples to dict for JSON serialization
            feature_importance_dict = {feature: float(importance) for feature, importance in feature_importance}
            
            metrics_data = {
                "linear_regression": {
                    "model_type": "LinearRegression",
                    "r2": float(r2),
                    "rmse": float(rmse),
                    "mae": float(mae),
                    "training_samples": int(training_samples),
                    "feature_importance": feature_importance_dict
                }
            }
            # Read existing metrics if file exists
            if metrics_path.exists():
                try:
                    with open(metrics_path, 'r') as f:
                        existing_metrics = json.load(f)
                    existing_metrics.update(metrics_data)
                    metrics_data = existing_metrics
                except Exception as e:
                    logger.warning(f"Could not read existing metrics file: {e}")
            
            with open(metrics_path, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            logger.info(f"Model metrics saved to {metrics_path}")
        
        return results
    
    def train_all_models(self) -> Dict[str, Dict[str, Any]]:
        """Train all models and compare performance"""
        logger.info("Training all models for comparison...")
        
        results = {}
        
        # Train Random Forest
        try:
            results["random_forest"] = self.train_random_forest()
        except Exception as e:
            logger.error(f"Error training Random Forest: {e}")
            results["random_forest"] = {"error": str(e)}
        
        # Train GBT
        try:
            results["gbt"] = self.train_gbt()
        except Exception as e:
            logger.error(f"Error training GBT: {e}")
            results["gbt"] = {"error": str(e)}
        
        # Train Linear Regression
        try:
            results["linear_regression"] = self.train_linear_regression()
        except Exception as e:
            logger.error(f"Error training Linear Regression: {e}")
            results["linear_regression"] = {"error": str(e)}
        
        # Compare models
        logger.info("\n" + "=" * 60)
        logger.info("Model Comparison Summary")
        logger.info("=" * 60)
        
        for model_name, result in results.items():
            if "error" not in result:
                logger.info(f"\n{model_name.upper()}:")
                logger.info(f"  RMSE: ${result['rmse']:.2f}")
                logger.info(f"  MAE: ${result['mae']:.2f}")
                logger.info(f"  R²: {result['r2']:.4f}")
        
        # Find best model
        best_model = None
        best_r2 = -float('inf')
        for model_name, result in results.items():
            if "error" not in result and result.get("r2", -float('inf')) > best_r2:
                best_r2 = result["r2"]
                best_model = model_name
        
        if best_model:
            logger.info(f"\n✅ Best Model: {best_model} (R² = {best_r2:.4f})")
        
        return results


def run_ml_training(spark: SparkSession, df=None) -> Dict[str, Dict[str, Any]]:
    """Run ML training pipeline"""
    logger.info("Starting ML training pipeline...")
    
    trainer = MLModelTrainer(spark)
    if df is not None:
        trainer.df = df
    results = trainer.train_all_models()
    
    logger.info(f"Models saved to: {trainer.models_dir}")
    return results

