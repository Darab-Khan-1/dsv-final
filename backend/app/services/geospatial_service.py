from typing import Dict, Any
from app.core.spark_session import get_spark_session
from app.core.config import settings
from app.utils.spark_imports import get_spark_functions, get_spark_ml
from src.config import PROCESSED_DATA_DIR, DATA_DIR
import logging

logger = logging.getLogger(__name__)


class GeospatialAnalysisService:
    def __init__(self):
        self._spark = None
        self.data_path = str(PROCESSED_DATA_DIR / "cleaned_data.parquet")
        self.zone_stats_path = str(DATA_DIR / "aggregates" / "geospatial_zone_stats.parquet")
        self.route_pairs_path = str(DATA_DIR / "aggregates" / "route_pairs_top.parquet")
    
    @property
    def spark(self):
        if self._spark is None:
            self._spark = get_spark_session()
        return self._spark
    
    async def get_pickup_hotspots(
        self,
        top_n: int = 20,
        min_trips: int = 100
    ) -> Dict[str, Any]:
        try:
            import os
            F = get_spark_functions()
            
            if os.path.exists(self.zone_stats_path):
                df = self.spark.read.parquet(self.zone_stats_path)
                
                result = df \
                    .groupBy("pickup_lat_grid", "pickup_lon_grid") \
                    .agg(F.sum("trip_count").alias("trip_count")) \
                    .filter(F.col("trip_count") >= min_trips) \
                    .orderBy(F.desc("trip_count")) \
                    .limit(top_n) \
                    .collect()
            else:
                df = self.spark.read.parquet(self.data_path)
                result = df \
                    .withColumn("pickup_lat_grid", F.round(F.col("pickup_latitude"), 2)) \
                    .withColumn("pickup_lon_grid", F.round(F.col("pickup_longitude"), 2)) \
                    .groupBy("pickup_lat_grid", "pickup_lon_grid") \
                    .agg(F.count("*").alias("trip_count")) \
                    .filter(F.col("trip_count") >= min_trips) \
                    .orderBy(F.desc("trip_count")) \
                    .limit(top_n) \
                    .collect()
            
            return {
                "data": [
                    {
                        "latitude": float(row.pickup_lat_grid),
                        "longitude": float(row.pickup_lon_grid),
                        "trip_count": int(row.trip_count)
                    }
                    for row in result
                ]
            }
        except Exception as e:
            logger.error(f"Error in get_pickup_hotspots: {e}")
            raise
    
    async def get_dropoff_hotspots(
        self,
        top_n: int = 20,
        min_trips: int = 100
    ) -> Dict[str, Any]:
        try:
            import os
            F = get_spark_functions()
            
            if os.path.exists(self.zone_stats_path):
                df = self.spark.read.parquet(self.zone_stats_path)
                
                result = df \
                    .groupBy("dropoff_lat_grid", "dropoff_lon_grid") \
                    .agg(F.sum("trip_count").alias("trip_count")) \
                    .filter(F.col("trip_count") >= min_trips) \
                    .orderBy(F.desc("trip_count")) \
                    .limit(top_n) \
                    .collect()
            else:
                df = self.spark.read.parquet(self.data_path)
                result = df \
                    .withColumn("dropoff_lat_grid", F.round(F.col("dropoff_latitude"), 2)) \
                    .withColumn("dropoff_lon_grid", F.round(F.col("dropoff_longitude"), 2)) \
                    .groupBy("dropoff_lat_grid", "dropoff_lon_grid") \
                    .agg(F.count("*").alias("trip_count")) \
                    .filter(F.col("trip_count") >= min_trips) \
                    .orderBy(F.desc("trip_count")) \
                    .limit(top_n) \
                    .collect()
            
            return {
                "data": [
                    {
                        "latitude": float(row.dropoff_lat_grid),
                        "longitude": float(row.dropoff_lon_grid),
                        "trip_count": int(row.trip_count)
                    }
                    for row in result
                ]
            }
        except Exception as e:
            logger.error(f"Error in get_dropoff_hotspots: {e}")
            raise
    
    async def get_route_pairs(self, top_n: int = 20) -> Dict[str, Any]:
        try:
            import os
            F = get_spark_functions()
            
            if os.path.exists(self.route_pairs_path):
                df = self.spark.read.parquet(self.route_pairs_path)
                
                result = df \
                    .orderBy(F.desc("trip_count")) \
                    .limit(top_n) \
                    .collect()
                
                return {
                    "data": [
                        {
                            "pickup": f"{row.pickup_lat_grid},{row.pickup_lon_grid}",
                            "dropoff": f"{row.dropoff_lat_grid},{row.dropoff_lon_grid}",
                            "trip_count": int(row.trip_count)
                        }
                        for row in result
                    ]
                }
            else:
                df = self.spark.read.parquet(self.data_path)
                result = df \
                    .withColumn("pickup_grid", F.concat(
                        F.round(F.col("pickup_latitude"), 2),
                        F.lit(","),
                        F.round(F.col("pickup_longitude"), 2)
                    )) \
                    .withColumn("dropoff_grid", F.concat(
                        F.round(F.col("dropoff_latitude"), 2),
                        F.lit(","),
                        F.round(F.col("dropoff_longitude"), 2)
                    )) \
                    .groupBy("pickup_grid", "dropoff_grid") \
                    .agg(F.count("*").alias("trip_count")) \
                    .orderBy(F.desc("trip_count")) \
                    .limit(top_n) \
                    .collect()
                
                return {
                    "data": [
                        {
                            "pickup": row.pickup_grid,
                            "dropoff": row.dropoff_grid,
                            "trip_count": int(row.trip_count)
                        }
                        for row in result
                    ]
                }
        except Exception as e:
            logger.error(f"Error in get_route_pairs: {e}")
            raise
    
    async def get_zone_comparison(self, zone_type: str) -> Dict[str, Any]:
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.data_path)
            
            airport_coords = {
                "JFK": {"lat": 40.6413, "lon": -73.7781},
                "LGA": {"lat": 40.7769, "lon": -73.8730},
            }
            
            airport_radius = 0.05
            
            if zone_type == "airport":
                results = {}
                for airport, coords in airport_coords.items():
                    airport_trips = df.filter(
                        (F.col("pickup_latitude") >= coords["lat"] - airport_radius) &
                        (F.col("pickup_latitude") <= coords["lat"] + airport_radius) &
                        (F.col("pickup_longitude") >= coords["lon"] - airport_radius) &
                        (F.col("pickup_longitude") <= coords["lon"] + airport_radius)
                    )
                    
                    stats = airport_trips.agg(
                        F.count("*").alias("trip_count"),
                        F.avg("fare_amount").alias("avg_fare"),
                        F.avg("trip_distance").alias("avg_distance"),
                        F.avg("trip_duration_minutes").alias("avg_duration")
                    ).collect()[0]
                    
                    results[airport] = {
                        "trip_count": stats.trip_count,
                        "avg_fare": stats.avg_fare,
                        "avg_distance": stats.avg_distance,
                        "avg_duration": stats.avg_duration
                    }
                
                city_avg = df.agg(
                    F.avg("fare_amount").alias("avg_fare"),
                    F.avg("trip_distance").alias("avg_distance")
                ).collect()[0]
                
                return {
                    "airports": results,
                    "city_average": {
                        "avg_fare": city_avg.avg_fare,
                        "avg_distance": city_avg.avg_distance
                    }
                }
            else:
                return {"message": f"Zone type {zone_type} not yet implemented"}
        except Exception as e:
            logger.error(f"Error in get_zone_comparison: {e}")
            raise
    
    async def get_clusters(
        self,
        n_clusters: int = 20,
        cluster_type: str = "kmeans"
    ) -> Dict[str, Any]:
        try:
            F = get_spark_functions()
            ml_modules = get_spark_ml()
            KMeans = ml_modules["KMeans"]
            VectorAssembler = ml_modules["VectorAssembler"]
            
            df = self.spark.read.parquet(self.data_path)
            
            df_sample = df.sample(0.15, seed=42)
            df_sample = df_sample.repartition(200)
            
            assembler = VectorAssembler(
                inputCols=["pickup_latitude", "pickup_longitude"],
                outputCol="features"
            )
            df_features = assembler.transform(df_sample)
            
            kmeans = KMeans(k=n_clusters, seed=42, featuresCol="features", predictionCol="cluster_id")
            model = kmeans.fit(df_features)
            df_clustered = model.transform(df_features)
            
            cluster_stats = df_clustered.groupBy("cluster_id").agg(
                F.count("*").alias("trip_count"),
                F.avg("pickup_latitude").alias("avg_lat"),
                F.avg("pickup_longitude").alias("avg_lon"),
                F.avg("fare_amount").alias("avg_fare")
            ).orderBy(F.desc("trip_count")).collect()
            
            return {
                "clusters": [
                    {
                        "cluster_id": row.cluster_id,
                        "trip_count": row.trip_count,
                        "latitude": row.avg_lat,
                        "longitude": row.avg_lon,
                        "avg_fare": row.avg_fare
                    }
                    for row in cluster_stats
                ],
                "cluster_type": cluster_type,
                "n_clusters": n_clusters
            }
        except Exception as e:
            logger.error(f"Error in get_clusters: {e}")
            raise
    
    async def get_spatial_density(self, grid_size: float = 0.01) -> Dict[str, Any]:
        try:
            F = get_spark_functions()
            df = self.spark.read.parquet(self.data_path)
            
            result = (df
                .withColumn("lat_grid", F.round(F.col("pickup_latitude") / grid_size) * grid_size)
                .withColumn("lon_grid", F.round(F.col("pickup_longitude") / grid_size) * grid_size)
                .groupBy("lat_grid", "lon_grid")
                .agg(F.count("*").alias("density"))
                .filter(F.col("density") > 10)
                .orderBy(F.desc("density"))
                .limit(100)
                .collect())
            
            return {
                "data": [
                    {
                        "latitude": row.lat_grid,
                        "longitude": row.lon_grid,
                        "density": row.density
                    }
                    for row in result
                ],
                "grid_size": grid_size
            }
        except Exception as e:
            logger.error(f"Error in get_spatial_density: {e}")
            raise

