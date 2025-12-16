import { apiClient } from '../client';

export interface ModelMetrics {
  model_type: string;
  r2: number;
  rmse: number;
  mae: number;
  training_samples: number;
  training_samples_display: string;
  feature_importance?: Record<string, number>;
}

export const getModelMetrics = async (modelName: string = 'random_forest') => {
  const response = await apiClient.get<ModelMetrics>('/ml/model-metrics', {
    params: { model_name: modelName }
  });
  return response.data;
};

export const getFeatureImportance = async (modelName: string = 'random_forest') => {
  const response = await apiClient.get('/ml/feature-importance', {
    params: { model_name: modelName }
  });
  return response.data;
};

export const predictFare = async (params: {
  pickup_datetime: string;
  pickup_latitude: number;
  pickup_longitude: number;
  dropoff_latitude: number;
  dropoff_longitude: number;
  passenger_count: number;
  trip_distance?: number;
}) => {
  const response = await apiClient.post('/ml/predict-fare', params);
  return response.data;
};

