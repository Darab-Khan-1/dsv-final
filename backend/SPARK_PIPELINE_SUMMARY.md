## Spark Pipeline Summary – NYC Taxi Data (Temporal, Geospatial, Economic)

This project uses **PySpark** to process a **large NYC yellow taxi dataset (~47M rows, ~6.9GB CSV)** on a **single laptop** (Dell Inspiron 15, 16GB RAM, 8 logical cores). The goal is to generate **data-science grade reporting** for **temporal, geospatial, and economic analysis**, while staying within tight memory and disk limits.

---

### 1. Overall Architecture

- **Backend-only processing**:
  - All heavy data work (ingestion, cleaning, analysis, ML) is done in Spark inside the `backend/` folder.
  - The **frontend** consumes **compact JSON outputs** and **model endpoints** for visualization, so we don’t generate heavy plots in Spark anymore.
- **Stages** (all Spark-based):
  - **Stage 1 – Ingestion**: CSV → Parquet in `backend/data/processed/raw_ingested/`
  - **Stage 2 – Cleaning**: Validity filters + feature columns → `backend/data/processed/cleaned_data.parquet`
  - **Stage 3 – Analysis**:
    - Temporal: trends by hour/day/month, duration distributions, fare trends.
    - Geospatial: hotspots, route pairs, airport/boundary analyses.
    - Economic: fare–distance correlations, tip behavior, revenue patterns, market share.
  - **Stage 4 – ML (optional)**: Fare prediction models (currently focused on linear regression).
- **Outputs**:
  - **Analysis JSON** in `backend/data/output/` (e.g. `temporal_analysis_results.json`, `geospatial_analysis_results.json`, `economic_analysis_results.json`).
  - **Models** in `backend/models/`.

---

### 2. Spark Configuration – Tuned for 16GB RAM / 47M Rows

Defined in `src/config.py` (`SPARK_CONFIG`):

- **Memory**:
  - `spark.executor.memory = 4g` (main workhorse)
  - `spark.driver.memory = 1g` (collects limited results)
  - `spark.memory.fraction = 0.6` and `spark.memory.storageFraction = 0.2`
    - Most heap is reserved for **execution**, **not caching**.
    - Caching is used sparingly and only for small aggregates.
- **CPU & parallelism**:
  - `spark.master = local[6]` → use 6 cores, leave 2 for OS/other processes.
  - `spark.sql.shuffle.partitions = 60`, `spark.default.parallelism = 60`
    - ~10× cores: good parallelism without overloading memory.
- **Adaptive Query Execution (AQE)**:
  - Enabled (`spark.sql.adaptive.enabled = true`) with coalescing and skew handling.
  - Broadcast joins limited to small tables (`10MB` thresholds) to avoid huge broadcasts.
- **Serialization & compression**:
  - Kryo serializer (`spark.serializer = KryoSerializer`) with capped buffers.
  - Snappy compression for Parquet, RDD/shuffle compression enabled.
- **Spilling & storage**:
  - `spark.storage.level = MEMORY_AND_DISK_SER`
  - Aggressive **spill-to-disk** when memory is tight instead of dying with OOM.

**Key principle**: _We deliberately under-allocate Spark memory_ on a 16GB machine to avoid crashing the OS, and we let Spark spill to disk when needed.

---

### 3. Processing Strategy – Sampling & Partitioning

Defined in `src/config.py` (`PROCESSING_CONFIG` and helpers):

- **Never fully materialize 47M rows in memory**:
  - `auto_sample_threshold = 5_000_000`
  - `force_sample_above = 30_000_000`
  - Large operations **always run on a sample**, not the full dataset.
- **Per-operation sampling** (`get_sample_strategy`):
  - **Analysis**:
    - Target: **10% sample**, capped at **5M rows**.
    - This is still statistically rich but fits comfortably in RAM.
  - **ML Training**:
    - Fixed **500K-row sample**, never >1M rows.
    - Enough for robust models, cheap enough for local hardware.
  - **Visualization (when we used Spark plots)**:
    - Hard cap at ~**50K points** sent to the driver for `toPandas()`.
    - Now visualizations are handled in the frontend, but this principle remains.
- **Optimal partitions** (`get_optimal_partitions`):
  - ~**500K–1M rows per partition**.
  - For ~47M rows, partitions are capped at **≤100**, avoiding thousands of tiny tasks that waste memory.
- **Caching policy** (`should_cache_dataframe`):
  - **Do NOT cache full 47M-row DataFrames**.
  - Only cache **small aggregates** (`< 500K` rows), e.g. hourly counts, zone-level summaries.

---

### 4. Stage-by-Stage Use of Spark

#### 4.1 Ingestion (`src/data_ingestion/ingest.py`)

- **Explicit schema** for CSV → avoids costly type inference on 47M rows.
- Adds `year`, `month` columns for partitioning.
- Writes to **Parquet** with partitioning by `(year, month)`:
  - Enables **predicate pushdown** and efficient reads for subsets.

#### 4.2 Cleaning (`src/data_cleaning/clean.py`)

- Fully Spark-based filtering:
  - Duration (1–180 min), distance (0.1–100 miles), fare, passenger count, NYC geographic bounds.
- Adds:
  - **Temporal features**: hour, day-of-week, month, year.
  - **Geospatial grids**: rounded lat/lon for hotspots.
- Writes cleaned Parquet to `backend/data/processed/cleaned_data.parquet`, still partitioned by time for fast slicing.

#### 4.3 Temporal Analysis (`src/temporal_analysis/analyze.py`)

- Operates on **Spark DataFrames**, not Pandas:
  - `groupBy` + `agg` for:
    - Trips by hour/day/month.
    - Duration distributions (using `percentile_approx`).
    - Fare trends by hour/month.
- **Collects only small aggregated results** to Python:
  - Result sets are thousands of rows, not millions.
  - Saved as compact JSON for the frontend.

#### 4.4 Geospatial Analysis (`src/geospatial_analysis/analyze.py`)

- Uses **lat/lon grids** (rounded coordinates) as zones.
- Computes:
  - Pickup/drop-off hotspots.
  - Route pairs between grid cells.
  - Airport-related stats using `AIRPORT_COORDINATES`.
- All heavy joins and aggregations stay inside Spark; only the **final zone-level table** is collected and persisted to JSON.

#### 4.5 Economic Analysis (`src/economic_analysis/analyze.py`)

- Pure Spark aggregation for:
  - Fare–distance–duration correlations.
  - Tip analysis by payment type, hour, distance bucket.
  - Revenue by hour, location, and segment.
  - Market share across key segments.
- Outputs:
  - A **small set of aggregated tables** saved as `economic_analysis_results.json` (and friends), optimized for fast API responses and frontend plotting.

#### 4.6 ML (Fare Prediction) (`src/ml_model/train.py`)

- Uses **Spark MLlib** on a **sampled, cleaned DataFrame**:
  - Features engineered in Spark (temporal + distance + geospatial).
  - Training sample capped at **300K–500K rows**.
- Models:
  - Currently emphasizes **Linear Regression** (lightweight, interpretable).
  - Heavier models (RF/GBT) are disabled by default for local-RAM safety.
- Models are saved in `backend/models/` and will be served via FastAPI endpoints.

---

### 5. Why This Is “Optimal” for Your Setup

Given:
- **47M rows** (4 big CSVs; ~6.9GB raw).
- **16GB RAM laptop**, with the OS and browser also using memory.

We chose:

- **Moderate Spark memory (4g executor + 1g driver)**:
  - Avoids JVM OOM and keeps the OS stable.
- **Sampling everywhere it matters**:
  - Analyses and models work on carefully chosen samples that are:
    - Big enough for statistical power.
    - Small enough to fit comfortably in memory.
- **Spark-first, Pandas-last**:
  - All heavy logic runs in Spark on **distributed DataFrames**.
  - We only convert **small results** to Python/JSON for:
    - API responses.
    - Frontend visualizations.
- **Local-friendly design**:
  - No assumption of a cluster.
  - Works end-to-end on a single laptop with careful resource control.

---

### 6. How the Frontend/Backend Use These Results

- **Backend (FastAPI)**:
  - Reads the **precomputed JSON outputs** and **Spark ML models**.
  - Exposes REST endpoints like:
    - `/api/v1/temporal/...`
    - `/api/v1/geospatial/...`
    - `/api/v1/economic/...`
    - `/api/v1/ml/predict`
  - Endpoints return **small JSON payloads** ready for charts.

- **Frontend**:
  - Does **all visualization** (line charts, bar charts, heatmaps, maps) in the browser.
  - This keeps Spark focused on what it’s best at: **large-scale computation**, not plotting.

---

### 7. How to Describe This in a Report

You can summarize our Spark strategy in one paragraph:

> “We used PySpark to ingest, clean, and analyze a 47M-row NYC taxi dataset on a single 16GB RAM laptop by combining conservative Spark memory settings with aggressive sampling, partition tuning, and Parquet-based storage. All heavy computations (temporal, geospatial, and economic aggregations, as well as ML feature engineering) are performed in Spark DataFrames, and only small aggregated tables (a few thousand rows) are collected to Python and exposed as JSON APIs. Visualizations are rendered on the frontend, while Spark remains dedicated to scalable, memory-safe data processing.”


