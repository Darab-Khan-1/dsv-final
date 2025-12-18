"""
Main execution script for NYC Taxi Data Analysis
Runs all stages of the pipeline
"""

import argparse
import logging
from pathlib import Path
from typing import Optional

from src.utils.spark_utils import create_spark_session, stop_spark_session
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DATA_DIR
from src.data_ingestion.ingest import ingest_all_csv_files
from src.data_cleaning.clean import clean_data
from src.temporal_analysis.analyze import run_temporal_analysis
from src.geospatial_analysis.analyze import run_geospatial_analysis
from src.economic_analysis.analyze import run_economic_analysis
from src.ml_model.train import run_ml_training

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_stage_completion(stage_path: Path) -> bool:
    """Check if a pipeline stage has already been completed."""
    return stage_path.exists() and any(stage_path.iterdir())


def main(
    skip_ingestion: bool = False,
    skip_cleaning: bool = False,
    sample_fraction: Optional[float] = None,
    run_stages: Optional[list] = None,
):
    """Main execution function (optimized, stage-aware, sampling-capable)."""
    logger.info("=" * 60)
    logger.info("NYC Taxi Data Analysis Pipeline (Optimized)")
    logger.info("=" * 60)

    if sample_fraction:
        logger.info(f"Running with {sample_fraction*100:.1f}% data sample")

    spark = create_spark_session("NYC_Taxi_Pipeline")

    try:
        # Stage 1: Ingestion (optional skip)
        ingested_path = PROCESSED_DATA_DIR / "raw_ingested"
        if skip_ingestion and check_stage_completion(ingested_path):
            logger.info("\n" + "=" * 60)
            logger.info("STAGE 1: Data Ingestion (SKIPPED - Using cached)")
            logger.info("=" * 60)
            logger.info(f"Using existing data: {ingested_path}")
        else:
            logger.info("\n" + "=" * 60)
            logger.info("STAGE 1: Data Ingestion (CSV to Parquet)")
            logger.info("=" * 60)
            ingested_path = ingest_all_csv_files(
                spark,
                input_dir=RAW_DATA_DIR,
                output_dir=ingested_path,
            )
            logger.info(f"Stage 1 complete. Data ingested to: {ingested_path}")

        # Stage 2: Cleaning (optional skip)
        cleaned_path = PROCESSED_DATA_DIR / "cleaned_data.parquet"
        if skip_cleaning and check_stage_completion(cleaned_path):
            logger.info("\n" + "=" * 60)
            logger.info("STAGE 2: Data Cleaning (SKIPPED - Using cached)")
            logger.info("=" * 60)
            logger.info(f"Using existing cleaned data: {cleaned_path}")
        else:
            logger.info("\n" + "=" * 60)
            logger.info("STAGE 2: Data Cleaning")
            logger.info("=" * 60)
            cleaned_path = clean_data(
                spark,
                input_path=ingested_path,
                output_path=cleaned_path,
            )
            logger.info(f"Stage 2 complete. Cleaned data: {cleaned_path}")

        # Load cleaned data once
        logger.info("\n📊 Loading cleaned data into memory...")
        df = spark.read.parquet(str(cleaned_path))

        # Optional sampling for dev/ML/viz
        if sample_fraction and sample_fraction < 1.0:
            df = df.sample(fraction=sample_fraction, seed=42)
            logger.info(f"Sampled to {sample_fraction*100:.1f}% of data")

        df.cache()
        total_rows = df.count()
        logger.info(f"Loaded {total_rows:,} rows into memory (cached)")

        stages_to_run = run_stages or ["temporal", "geospatial", "economic", "viz", "ml"]

        temporal_results = []
        geospatial_results = []
        economic_results = []
        ml_results = []

        # Stage 3: Analysis
        logger.info("\n" + "=" * 60)
        logger.info("STAGE 3: Data Analysis")
        logger.info("=" * 60)

        if "temporal" in stages_to_run:
            logger.info("\n--- 3.1 Temporal Analysis ---")
            temporal_results = run_temporal_analysis(spark, df=df)
            logger.info("Temporal analysis complete")

        if "geospatial" in stages_to_run:
            logger.info("\n--- 3.2 Geospatial Analysis ---")
            geospatial_results = run_geospatial_analysis(spark, df=df)
            logger.info("Geospatial analysis complete")

        if "economic" in stages_to_run:
            logger.info("\n--- 3.3 Economic Analysis ---")
            economic_results = run_economic_analysis(spark, df=df)
            logger.info("Economic analysis complete")

        # Stage 4: ML (use dedicated 30% sample if dataset is huge)
        if "ml" in stages_to_run:
            logger.info("\n" + "=" * 60)
            logger.info("STAGE 5: Machine Learning - Fare Prediction")
            logger.info("=" * 60)
            ml_df = df
            if total_rows > 1_000_000:
                ml_df = df.sample(fraction=0.3, seed=42)
                logger.info(f"Using 30% sample for ML ({ml_df.count():,} rows)")
            ml_results = run_ml_training(spark, df=ml_df)
            logger.info("ML model training complete")

        # Unpersist cache
        df.unpersist()

        logger.info("\n" + "=" * 60)
        logger.info("Pipeline execution complete!")
        logger.info("=" * 60)
        logger.info("\nSummary:")
        logger.info(f"  - Total rows processed: {total_rows:,}")
        logger.info(f"  - Temporal analysis: {len(temporal_results)} result sets")
        logger.info(f"  - Geospatial analysis: {len(geospatial_results)} result sets")
        logger.info(f"  - Economic analysis: {len(economic_results)} result sets")
        logger.info(f"  - ML Models: {len(ml_results)} models trained")
        logger.info("\nResults saved to:")
        logger.info(f"  - Analysis results: {OUTPUT_DATA_DIR}/")
        logger.info(f"  - ML Models: models/")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise
    finally:
        stop_spark_session(spark)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NYC Taxi Data Pipeline")
    parser.add_argument("--skip-ingestion", action="store_true", help="Skip data ingestion if already done")
    parser.add_argument("--skip-cleaning", action="store_true", help="Skip data cleaning if already done")
    parser.add_argument("--sample", type=float, default=None, help="Sample fraction (0.0-1.0) for faster processing")
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=["temporal", "geospatial", "economic", "ml"],
        help="Specific stages to run",
    )

    args = parser.parse_args()

    main(
        skip_ingestion=args.skip_ingestion,
        skip_cleaning=args.skip_cleaning,
        sample_fraction=args.sample,
        run_stages=args.stages,
    )

