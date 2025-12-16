# NYC Taxi Data Analysis - FastAPI Backend

REST API backend for serving Spark analysis results from NYC taxi data.

## 🚀 Quick Start

2025-12-15 06:38:29,606 - src.visualization.visualize - INFO - Loading data from /home/darab/Downloads/archive (1) (1)/data/processed/cleaned_data.parquet
2025-12-15 06:38:29,865 - src.visualization.visualize - INFO - Loaded 24,030,086 reco
### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the backend directory:

```env
DATA_DIR=../data
PROCESSED_DATA_DIR=../data/processed
OUTPUT_DATA_DIR=../data/output
MODELS_DIR=../models
SPARK_MASTER=local[*]
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### Run the Server

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the main file
python -m app.main
```

### API Documentation

Once the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📁 Project Structure

```
backend/
├── app/                         # FastAPI application
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py     # API router
│   │       └── endpoints/      # API endpoints
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   └── spark_session.py    # Spark session management
│   ├── services/               # Business logic
│   └── schemas/                # Request/Response schemas
├── src/                         # Data processing pipeline
│   ├── data_ingestion/         # Stage 1: CSV to Parquet
│   ├── data_cleaning/          # Stage 2: Data cleaning
│   ├── temporal_analysis/      # Stage 3.1: Temporal analysis
│   ├── geospatial_analysis/   # Stage 3.2: Geospatial analysis
│   ├── economic_analysis/      # Stage 3.3: Economic analysis
│   ├── utils/                  # Utility functions
│   └── config.py               # Pipeline configuration
├── main.py                      # Main pipeline execution
├── tests/                       # Unit tests
├── scripts/                     # Utility scripts
├── requirements.txt
└── README.md
```

## 🔌 API Endpoints

### Health
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/spark` - Spark session health

### Temporal Analysis
- `GET /api/v1/temporal/trips-by-hour` - Trips by hour
- `GET /api/v1/temporal/trips-by-day` - Trips by day of week
- `GET /api/v1/temporal/trips-by-month` - Trips by month
- `GET /api/v1/temporal/peak-hours` - Peak pickup hours
- `GET /api/v1/temporal/duration-distribution` - Duration statistics
- `GET /api/v1/temporal/fare-trends` - Fare trends over time

### Geospatial Analysis
- `GET /api/v1/geospatial/pickup-hotspots` - Top pickup locations
- `GET /api/v1/geospatial/dropoff-hotspots` - Top dropoff locations
- `GET /api/v1/geospatial/route-pairs` - Common route pairs
- `GET /api/v1/geospatial/zone-comparison` - Zone comparison
- `GET /api/v1/geospatial/clusters` - Geospatial clusters
- `GET /api/v1/geospatial/spatial-density` - Density heatmap

### Economic Analysis
- `GET /api/v1/economic/correlations` - Correlation matrix
- `GET /api/v1/economic/tip-analysis` - Tip behavior analysis
- `GET /api/v1/economic/revenue-analysis` - Revenue analysis
- `GET /api/v1/economic/price-elasticity` - Price elasticity
- `GET /api/v1/economic/surge-pricing` - Surge pricing detection
- `GET /api/v1/economic/customer-segments` - Customer segmentation
- `GET /api/v1/economic/market-share` - Vendor market share

### Machine Learning
- `POST /api/v1/ml/predict-fare` - Predict taxi fare
- `GET /api/v1/ml/model-info` - Model information
- `GET /api/v1/ml/feature-importance` - Feature importance

### Data
- `GET /api/v1/data/summary` - Dataset summary
- `GET /api/v1/data/sample` - Sample data
- `GET /api/v1/data/date-range` - Available date range

## 🛠️ Development

### Code Style
- Follow PEP 8
- Use type hints
- Document functions with docstrings

### Testing
```bash
# Run tests
pytest tests/
```

### Logging
Logging is configured in `app/main.py`. Logs include:
- API requests
- Spark operations
- Errors and exceptions

## 📝 Notes

- Spark session is managed as a singleton
- Services handle business logic
- Endpoints are thin wrappers around services
- Configuration is environment-based
- CORS is enabled for frontend integration

## 🔧 Troubleshooting

### Spark Session Issues
- Ensure Java is installed
- Check SPARK_MASTER configuration
- Verify data paths are correct

### Data Not Found
- Ensure processed data exists in `PROCESSED_DATA_DIR`
- Check file permissions
- Verify Parquet file format

## 📚 Next Steps

1. Implement remaining service methods
2. Add caching layer (Redis)
3. Add authentication/authorization
4. Add rate limiting
5. Add monitoring and metrics
6. Add comprehensive tests

