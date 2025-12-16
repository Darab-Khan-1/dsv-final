# Advanced Analytics Modules

This package contains higher–level analytics built on top of the
pre-aggregated Parquet tables in `backend/data/aggregates`.

## Modules

- `demand_forecast.py`: Forecast hourly trip demand using temporal aggregates.
- `route_optimization.py`: Identify inefficient routes based on duration vs distance.
- `surge_pricing.py`: Highlight time/zone combinations where surge pricing is promising.
- `customer_segments.py`: Derive customer segments from fare and tipping behavior.
- `revenue_optimization.py`: Surface high–value time windows for driver allocation.
- `anomaly_detection.py`: Flag unusual demand and route patterns.

## Runner

- `run_advanced_analytics.py`: Convenience script that executes all analysis modules and
  returns a consolidated JSON–serializable dictionary following the structure described in `plan.txt`.


