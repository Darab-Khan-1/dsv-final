"""
Lazy import utilities for PySpark
Allows backend to start even if PySpark is not installed
"""

def get_spark_functions():
    """Lazy import of PySpark SQL functions"""
    try:
        from pyspark.sql import functions as F
        return F
    except ImportError:
        raise ImportError(
            "PySpark is not installed. Install it with: pip install pyspark"
        )


def get_spark_window():
    """Lazy import of PySpark Window functions"""
    try:
        from pyspark.sql.window import Window
        return Window
    except ImportError:
        raise ImportError(
            "PySpark is not installed. Install it with: pip install pyspark"
        )


def get_spark_ml():
    """Lazy import of PySpark ML modules"""
    try:
        from pyspark.ml.stat import Correlation
        from pyspark.ml.feature import VectorAssembler, StandardScaler
        from pyspark.ml.clustering import KMeans
        from pyspark.ml.regression import (
            RandomForestRegressionModel,
            GBTRegressionModel,
            LinearRegressionModel
        )
        return {
            "Correlation": Correlation,
            "VectorAssembler": VectorAssembler,
            "StandardScaler": StandardScaler,
            "KMeans": KMeans,
            "RandomForestRegressionModel": RandomForestRegressionModel,
            "GBTRegressionModel": GBTRegressionModel,
            "LinearRegressionModel": LinearRegressionModel,
        }
    except ImportError:
        raise ImportError(
            "PySpark is not installed. Install it with: pip install pyspark"
        )


def get_spark_types():
    """Lazy import of PySpark types"""
    try:
        from pyspark.sql.types import (
            StructType, StructField, DoubleType, IntegerType,
            StringType, TimestampType
        )
        return {
            "StructType": StructType,
            "StructField": StructField,
            "DoubleType": DoubleType,
            "IntegerType": IntegerType,
            "StringType": StringType,
            "TimestampType": TimestampType,
        }
    except ImportError:
        raise ImportError(
            "PySpark is not installed. Install it with: pip install pyspark"
        )

