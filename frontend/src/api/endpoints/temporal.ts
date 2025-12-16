import { apiClient } from '../client';
import type { 
  TripsByHour, 
  TripsByDay, 
  TripsByMonth, 
  PeakHour, 
  DurationDistribution,
  FareTrend,
  TemporalFilters 
} from '../types';

export const getTripsByHour = async (params?: TemporalFilters) => {
  const response = await apiClient.get<{ data: TripsByHour[] }>('/temporal/trips-by-hour', { params });
  return response.data;
};

export const getTripsByDay = async (params?: Omit<TemporalFilters, 'day_of_week'>) => {
  const response = await apiClient.get<{ data: TripsByDay[] }>('/temporal/trips-by-day', { params });
  return response.data;
};

export const getTripsByMonth = async (params?: { year?: number }) => {
  const response = await apiClient.get<{ data: TripsByMonth[] }>('/temporal/trips-by-month', { params });
  return response.data;
};

export const getPeakHours = async (topN: number = 10) => {
  const response = await apiClient.get<{ data: PeakHour[] }>('/temporal/peak-hours', { 
    params: { top_n: topN } 
  });
  return response.data;
};

export const getDurationDistribution = async (params?: { year?: number; month?: number }) => {
  const response = await apiClient.get<DurationDistribution>('/temporal/duration-distribution', { params });
  return response.data;
};

export const getFareTrends = async (params?: { group_by?: 'hour' | 'day' | 'month'; year?: number }) => {
  const response = await apiClient.get<{ data: FareTrend[] }>('/temporal/fare-trends', { params });
  return response.data;
};
