import { apiClient } from '../client';
import type { HealthResponse } from '../types';

export const getHealth = async () => {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
};

export const getSparkHealth = async () => {
  const response = await apiClient.get<HealthResponse>('/health/spark');
  return response.data;
};
