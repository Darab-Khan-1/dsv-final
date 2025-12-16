// Health Types
export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  service?: string;
  spark_version?: string;
  error?: string;
}

// Temporal Types
export interface TripsByHour {
  hour: number;
  trip_count: number;
}

export interface TripsByDay {
  day_of_week: number;
  trip_count: number;
}

export interface TripsByMonth {
  year: number;
  month: number;
  trip_count: number;
}

export interface PeakHour {
  hour: number;
  trip_count: number;
}

export interface DurationDistribution {
  mean: number;
  stddev: number;
  min: number;
  max: number;
  median: number;
  p25: number;
  p75: number;
}

export interface FareTrend {
  hour?: number;
  year?: number;
  month?: number;
  avg_fare: number;
}

// Geospatial Types
export interface Hotspot {
  latitude: number;
  longitude: number;
  trip_count: number;
}

export interface RoutePair {
  pickup: string;
  dropoff: string;
  trip_count: number;
}

export interface Cluster {
  cluster_id: number;
  trip_count: number;
  latitude: number;
  longitude: number;
  avg_fare: number;
}

export interface SpatialDensity {
  latitude: number;
  longitude: number;
  density: number;
}

// Economic Types
export interface CorrelationMatrix {
  columns: string[];
  correlation_matrix: number[][];
}

export interface TipAnalysis {
  payment_type?: number;
  hour?: number;
  avg_tip_percent: number;
}

export interface RevenueData {
  hour?: number;
  avg_revenue: number;
}

export interface PriceElasticity {
  distance_bucket: string;
  avg_fare_per_mile: number;
  avg_fare: number;
  avg_distance: number;
  trip_count: number;
}

export interface SurgePricingHour {
  hour: number;
  surge_count: number;
  avg_surge_fare: number;
  avg_z_score: number;
}

export interface SurgePricing {
  total_surge_events: number;
  surge_percentage: number;
  top_surge_hours: SurgePricingHour[];
  threshold: number;
}

export interface EconomicInsights {
  highest_tip_hour: number | null;
  highest_tip_percent: number;
  best_revenue_hour: number | null;
  airport_premium: number;
  credit_card_tip_premium: number;
  credit_tip_rate: number;
  cash_tip_rate: number;
}

export interface CustomerSegment {
  segment: number;
  customer_count: number;
  avg_fare: number;
  avg_distance: number;
  avg_duration: number;
}

export interface MarketShare {
  vendor_id: number;
  trip_count: number;
  market_share_percent: number;
  avg_fare: number;
}

// ML Types
export interface FarePredictionRequest {
  pickup_datetime: string;
  pickup_latitude: number;
  pickup_longitude: number;
  dropoff_latitude: number;
  dropoff_longitude: number;
  passenger_count: number;
  trip_distance?: number;
}

export interface FarePredictionResponse {
  predicted_fare: number;
  confidence: number;
  model_used: string;
  features: Record<string, number>;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

// Data Types
export interface DataSummary {
  total_records: number;
  date_range: {
    start: string;
    end: string;
  };
  summary: {
    count: Record<string, number>;
    mean: Record<string, number>;
    stddev: Record<string, number>;
    min: Record<string, number>;
    max: Record<string, number>;
  };
}

export interface TripRecord {
  VendorID: number;
  tpep_pickup_datetime: string;
  tpep_dropoff_datetime: string;
  passenger_count: number;
  trip_distance: number;
  pickup_longitude: number;
  pickup_latitude: number;
  dropoff_longitude: number;
  dropoff_latitude: number;
  fare_amount: number;
  tip_amount: number;
  total_amount: number;
  payment_type: number;
  trip_duration_minutes: number;
}

export interface DateRange {
  min_date: string;
  max_date: string;
  min_year: number;
  max_year: number;
}

// Filter Types
export interface TemporalFilters {
  year?: number;
  month?: number;
  day_of_week?: number;
}
