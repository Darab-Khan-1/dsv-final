"""
Runner for all advanced analytics modules.
"""

from typing import Dict, Any

from .demand_forecast import run_demand_forecast
from .route_optimization import run_route_optimization
from .surge_pricing import run_surge_pricing
from .customer_segments import run_customer_segments
from .revenue_optimization import run_revenue_optimization
from .anomaly_detection import run_anomaly_detection


def run_all_analytics() -> Dict[str, Any]:
    return {
        "demand_forecast": run_demand_forecast(),
        "route_optimization": run_route_optimization(),
        "surge_pricing": run_surge_pricing(),
        "customer_segments": run_customer_segments(),
        "revenue_optimization": run_revenue_optimization(),
        "anomaly_detection": run_anomaly_detection(),
    }


if __name__ == "__main__":
    import json

    results = run_all_analytics()
    print(json.dumps(results, indent=2))


