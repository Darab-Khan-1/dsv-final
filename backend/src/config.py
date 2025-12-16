"""
Project Configuration for NYC Taxi Pipeline
Tuned for your Dell Inspiron 15 (16GB RAM, 8 cores) and ~47M rows (6.9GB CSV).
"""

from pathlib import Path
from typing import Dict, Any

# Backend root directory (store all data/reports/results inside backend)
PROJECT_ROOT = Path(__file__).parent.parent  # backend/

# Data directories (now inside backend/)
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DATA_DIR = DATA_DIR / "output"

# Models directory (inside backend/)
MODELS_DIR = PROJECT_ROOT / "models"

# Reports directory (inside backend/)
REPORTS_DIR = PROJECT_ROOT / "reports"

# Checkpoints for breaking lineage (inside backend/)
CHECKPOINT_DIR = DATA_DIR / "checkpoints"

# Spark configuration - Conservative for 47M rows on 16GB RAM
SPARK_CONFIG = {
    # === Memory Settings (Conservative for 47M rows) ===
    "spark.executor.memory": "4g",           # 4GB executor
    "spark.driver.memory": "1g",             # 1GB driver
    "spark.memory.fraction": "0.6",          # 60% for execution/storage
    "spark.memory.storageFraction": "0.2",   # 20% for cache (rest for execution)
    "spark.memory.offHeap.enabled": "false",
    
    # === Core Settings (8 logical cores available) ===
    # Use fewer cores/partitions to reduce concurrent memory pressure on laptop
    "spark.master": "local[3]",              # Use 3 cores (leave 5 for OS/other work)
    "spark.sql.shuffle.partitions": "24",    # ~8x cores instead of 10x
    "spark.default.parallelism": "24",
    "spark.executor.cores": "3",
    
    # === Adaptive Query Execution (CRITICAL for large datasets) ===
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.initialPartitionNum": "60",
    "spark.sql.adaptive.advisoryPartitionSizeInBytes": "128MB",
    "spark.sql.adaptive.autoBroadcastJoinThreshold": "10MB",
    "spark.sql.adaptive.skewJoin.enabled": "true",
    "spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes": "268435456",
    "spark.sql.adaptive.localShuffleReader.enabled": "true",
    
    # === Serialization (Efficient for large data) ===
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
    "spark.kryoserializer.buffer.max": "256m",
    "spark.kryoserializer.buffer": "64k",
    
    # === Compression (Save memory & disk) ===
    "spark.sql.parquet.compression.codec": "snappy",
    "spark.rdd.compress": "true",
    "spark.shuffle.compress": "true",
    "spark.shuffle.spill.compress": "true",
    
    # === File Handling (Optimized for 6.9GB dataset) ===
    "spark.sql.files.maxPartitionBytes": "134217728",      # 128MB chunks
    "spark.sql.files.openCostInBytes": "8388608",          # 8MB
    "spark.sql.files.maxRecordsPerFile": "1000000",        # 1M records per file
    
    # === Shuffle Optimization (Critical for 47M rows) ===
    "spark.shuffle.file.buffer": "64k",
    "spark.reducer.maxSizeInFlight": "64m",
    "spark.shuffle.sort.bypassMergeThreshold": "100",
    "spark.shuffle.spill.initialMemoryThreshold": "5242880",  # 5MB
    
    # === Storage (Spill to disk aggressively) ===
    "spark.storage.level": "MEMORY_AND_DISK_SER",
    "spark.storage.memoryMapThreshold": "2097152",  # 2MB
    
    # === GC Settings (Optimized for 4GB heap) ===
    "spark.executor.extraJavaOptions": (
        "-XX:+UseG1GC "
        "-XX:InitiatingHeapOccupancyPercent=30 "
        "-XX:MaxGCPauseMillis=200 "
        "-XX:G1HeapRegionSize=16m "
        "-XX:ConcGCThreads=2 "
        "-XX:ParallelGCThreads=6 "
        "-XX:+ParallelRefProcEnabled"
    ),
    "spark.driver.extraJavaOptions": "-XX:+UseG1GC -XX:InitiatingHeapOccupancyPercent=30",
    
    # === Result Limits ===
    "spark.driver.maxResultSize": "512m",
    
    # === SQL Optimization ===
    "spark.sql.codegen.wholeStage": "true",
    "spark.sql.codegen.maxFields": "100",
    "spark.sql.inMemoryColumnarStorage.compressed": "true",
    "spark.sql.inMemoryColumnarStorage.batchSize": "10000",
    
    # === Broadcast ===
    "spark.sql.autoBroadcastJoinThreshold": "10485760",  # 10MB

    # === Aggregation Strategy ===
    # Prefer sort-based aggregation over hash aggregation to reduce per-task memory usage
    "spark.sql.execution.useObjectHashAggregate": "false",
    "spark.sql.execution.aggregate.twoLevel.enabled": "false",
    
    # === UI ===
    "spark.ui.enabled": "true",
    "spark.ui.port": "4040",
    "spark.ui.retainedJobs": "50",
    "spark.ui.retainedStages": "50",
    
    # Disable dynamic allocation for predictability
    "spark.dynamicAllocation.enabled": "false",
    
    # Checkpointing path
    "spark.sql.streaming.checkpointLocation": "/tmp/spark-checkpoints",
}

# === Processing Strategy for ~47M Rows ===
PROCESSING_CONFIG = {
    # NEVER load full 47M rows into memory
    # More aggressive thresholds per plan.txt
    "auto_sample_threshold": 10_000_000,  # Sample if >10M rows
    "force_sample_above": 40_000_000,  # MUST sample if >40M rows

    # ML Training (sample to manageable size)
    "ml_sample_threshold": 2_000_000,  # Sample if >2M rows
    "ml_sample_size": 800_000,  # Target ~800K rows for ML
    "ml_max_rows": 1_000_000,  # Never exceed 1M for ML

    # Visualization (sample heavily)
    "viz_sample_size": 50_000,  # 50K points max

    # Analysis (use stratified sampling)
    # 25% sample, capped to 12M rows
    "analysis_sample_fraction": 0.25,
    "analysis_max_rows": 12_000_000,

    # Memory management
    "batch_size": 10_000,
    "max_memory_rows": 1_000_000,  # Never cache >1M rows

    # Checkpointing (CRITICAL for 47M rows)
    "enable_checkpointing": True,
    "checkpoint_frequency": 5_000_000,  # Checkpoint every 5M rows
    "checkpoint_during_cleaning": True,  # Checkpoint after cleaning

    # Cache strategy
    "disable_full_cache": True,  # NEVER cache full 47M rows
    "cache_aggregated_only": True,  # Only cache small aggregations
    "cache_threshold_rows": 500_000,  # Only cache if <500K rows
}

# Data cleaning thresholds
CLEANING_THRESHOLDS = {
    "trip_duration_min": 1,      # minutes
    "trip_duration_max": 180,    # minutes
    "trip_distance_min": 0.1,    # miles
    "trip_distance_max": 100,    # miles
    "fare_amount_min": 2.50,     # dollars
    "fare_amount_max": 500,      # dollars
    "passenger_count_min": 1,
    "passenger_count_max": 6,
    "nyc_lat_min": 40.5,
    "nyc_lat_max": 40.9,
    "nyc_lon_min": -74.3,
    "nyc_lon_max": -73.7,
}

# Airport coordinates (for zone detection)
AIRPORT_COORDINATES = {
    "JFK": {"lat": 40.6413, "lon": -73.7781, "radius_miles": 2.0},
    "LGA": {"lat": 40.7769, "lon": -73.8730, "radius_miles": 1.5},
    "EWR": {"lat": 40.6895, "lon": -74.1745, "radius_miles": 2.0},
}

# Simplified feature, ML, viz, logging configs (used by analysis/ML/viz modules)
FEATURE_CONFIG = {
    "time_features": ["hour", "day_of_week", "is_weekend"],
    "distance_features": ["trip_distance"],
    "categorical_features": ["payment_type", "rate_code"],
    "derived_features": ["speed_mph", "fare_per_mile"],
}

ML_CONFIG = {
    "test_size": 0.2,
    "random_state": 42,
    "cv_folds": 3,
    "models": {
        "linear_regression": True,
        "random_forest": False,
        "gradient_boosting": False,
    },
    "linear_regression": {
        "max_iter": 100,
        "reg_param": 0.01,
        "elastic_net_param": 0.5,
    },
}

VIZ_CONFIG = {
    "figure_size": (12, 8),
    "dpi": 100,
    "style": "seaborn-v0_8-darkgrid",
    "color_palette": "Set2",
    "save_formats": ["png"],
    "max_scatter_points": 10_000,
    "max_heatmap_cells": 10_000,
}

LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": REPORTS_DIR / "pipeline.log",
}

# Create directories if they don't exist
for directory in [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    OUTPUT_DATA_DIR,
    OUTPUT_DATA_DIR / "visualizations",
    OUTPUT_DATA_DIR / "analysis_results",
    MODELS_DIR,
    REPORTS_DIR,
    CHECKPOINT_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)


# === Helper Functions tuned for ~47M rows ===

def get_optimal_partitions(total_rows: int) -> int:
    """
    Optimal partitions for 47M row dataset
    Rule: ~500K-1M rows per partition
    """
    if total_rows < 1_000_000:
        return 10
    elif total_rows < 5_000_000:
        return 20
    elif total_rows < 10_000_000:
        return 40
    elif total_rows < 30_000_000:
        return 60
    else:
        # ~500-600K rows per partition
        return min(int(total_rows / 600_000), 100)


def get_sample_strategy(total_rows: int, operation: str) -> Dict[str, Any]:
    """
    Sampling strategy specifically for 47M row dataset.
    operation: 'full', 'ml', 'viz', 'analysis'
    """
    if operation == "full":
        if total_rows > PROCESSING_CONFIG["force_sample_above"]:
            return {
                "use_sample": True,
                "fraction": 0.2,
                "absolute_size": int(total_rows * 0.2),
                "reason": "Dataset >30M rows - forced sampling",
            }
        return {"use_sample": False, "fraction": 1.0, "absolute_size": total_rows}

    if operation == "ml":
        if total_rows > PROCESSING_CONFIG["ml_sample_threshold"]:
            fraction = min(PROCESSING_CONFIG["ml_sample_size"] / total_rows, 0.2)
            return {
                "use_sample": True,
                "fraction": fraction,
                "absolute_size": PROCESSING_CONFIG["ml_sample_size"],
                "reason": f"ML works best with {PROCESSING_CONFIG['ml_sample_size']:,} rows",
            }
        return {"use_sample": False, "fraction": 1.0, "absolute_size": total_rows}

    if operation == "viz":
        if total_rows > PROCESSING_CONFIG["viz_sample_size"]:
            fraction = PROCESSING_CONFIG["viz_sample_size"] / total_rows
            return {
                "use_sample": True,
                "fraction": fraction,
                "absolute_size": PROCESSING_CONFIG["viz_sample_size"],
                "reason": f"Visualization optimized for {PROCESSING_CONFIG['viz_sample_size']:,} points",
            }
        return {"use_sample": False, "fraction": 1.0, "absolute_size": total_rows}

    # analysis
    if total_rows > PROCESSING_CONFIG["auto_sample_threshold"]:
        sample_size = int(total_rows * PROCESSING_CONFIG["analysis_sample_fraction"])
        sample_size = min(sample_size, PROCESSING_CONFIG["analysis_max_rows"])
        fraction = sample_size / total_rows
        return {
            "use_sample": True,
            "fraction": fraction,
            "absolute_size": sample_size,
            "reason": f"Analysis on {sample_size:,} rows (10% sample)",
        }

    return {"use_sample": False, "fraction": 1.0, "absolute_size": total_rows}


def should_cache_dataframe(total_rows: int) -> bool:
    """Decide if a DataFrame is small enough to cache."""
    if PROCESSING_CONFIG["disable_full_cache"]:
        return total_rows <= PROCESSING_CONFIG["cache_threshold_rows"]
    return False


def get_processing_recommendation(total_rows: int) -> Dict[str, Any]:
    """High-level recommendation summary for docs/logs."""
    return {
        "total_rows": total_rows,
        "recommended_sample": "10% (~4.7M rows) for analysis",
        "ml_sample": "500K rows",
        "viz_sample": "50K rows",
        "estimated_time": {
            "ingestion": "15-20 minutes",
            "cleaning": "20-25 minutes",
            "analysis": "10-15 minutes",
            "ml": "5-10 minutes",
            "total": "50-70 minutes",
        },
        "memory_usage": {
            "peak": "4-5 GB",
            "steady": "3-4 GB",
        },
        "disk_usage": {
            "parquet": "~2.5 GB",
            "checkpoints": "~3 GB",
            "total_needed": "~6 GB",
        },
    }


def print_config_summary() -> None:
    """Print configuration summary for 47M rows."""
    rec = get_processing_recommendation(47_248_849)
    print("\n" + "=" * 80)
    print("  CONFIGURATION FOR ~47M ROW NYC TAXI DATASET")
    print("  Dell Inspiron 15 3511 | 16GB RAM | 8 CPU cores")
    print("=" * 80)
    print("\nDataset:")
    print("  • Total rows: 47,248,849")
    print("  • Raw size: 6.9 GB")
    print("  • Parquet size: ~2.5 GB")
    print("\nSpark Configuration:")
    print(f"  • Executor: {SPARK_CONFIG['spark.executor.memory']}")
    print(f"  • Driver: {SPARK_CONFIG['spark.driver.memory']}")
    print("  • Cores: 6 (of 8 available)")
    print("  • Partitions: 60–100")
    print("\nProcessing Strategy:")
    print(f"  • Analysis: {rec['recommended_sample']}")
    print(f"  • ML Training: {rec['ml_sample']}")
    print(f"  • Visualization: {rec['viz_sample']}")
    print("  • Caching: DISABLED for full dataset")
    print("\nExpected Performance:")
    for k, v in rec["estimated_time"].items():
        print(f"  • {k.capitalize()}: {v}")
    print("\nResource Usage:")
    print(f"  • Peak memory: {rec['memory_usage']['peak']}")
    print(f"  • Disk needed: {rec['disk_usage']['total_needed']}")
    print("\n⚠️  IMPORTANT:")
    print("  • Full dataset processing NOT recommended")
    print("  • Always use sampling for this dataset size")
    print("  • Close browser/heavy apps before running")
    print("  • Monitor: `watch -n 1 free -h`")
    print("=" * 80 + "\n")


def check_system_requirements() -> bool:
    """Check if system can handle ~47M rows with this config."""
    try:
        import psutil

        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(str(PROJECT_ROOT))

        total_ram_gb = mem.total / (1024**3)
        available_ram_gb = mem.available / (1024**3)
        disk_free_gb = disk.free / (1024**3)

        print("\n" + "=" * 80)
        print("  SYSTEM CHECK FOR ~47M ROW PROCESSING")
        print("=" * 80)
        print("\nMemory:")
        print(f"  • Total: {total_ram_gb:.1f} GB")
        print(f"  • Available: {available_ram_gb:.1f} GB")
        print("  • Required: ~6 GB minimum")
        print("\nDisk:")
        print(f"  • Free space: {disk_free_gb:.1f} GB")
        print("  • Required: ~6 GB for processing")

        issues = []
        if available_ram_gb < 6:
            issues.append("⚠️  Less than 6GB RAM available - close other apps")
        if disk_free_gb < 6:
            issues.append("⚠️  Less than 6GB disk space - cleanup needed")

        if issues:
            print("\n" + "=" * 80)
            print("  WARNINGS:")
            for issue in issues:
                print("  " + issue)
            print("=" * 80 + "\n")
            return False

        print("\n✅ System meets requirements for ~47M row processing")
        print("=" * 80 + "\n")
        return True

    except ImportError:
        print("ℹ️  Install psutil: pip install psutil\n")
        return True

