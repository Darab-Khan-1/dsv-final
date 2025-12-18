For virtual env
python -m venv venv
source venv/bin/activate 

# Install dependencies
pip install -r requirements.txt

# Run complete pipeline 
python3 main.py 

#generate aggregate tables.
python -m src.aggregation.create_aggregate_tables


# Run the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend 
npm install
npm run dev



## 🔌 API Endpoints

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

