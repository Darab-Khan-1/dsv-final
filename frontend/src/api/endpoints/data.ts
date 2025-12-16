import { apiClient } from '../client';
import type { DataSummary, TripRecord, DateRange } from '../types';

export const getDataSummary = async () => {
  const response = await apiClient.get<DataSummary>('/data/summary');
  return response.data;
};

export const getDataSample = async (params?: { n?: number; year?: number; month?: number }) => {
  const response = await apiClient.get<{ count: number; data: TripRecord[] }>('/data/sample', { params });
  return response.data;
};

export const getDateRange = async () => {
  const response = await apiClient.get<DateRange>('/data/date-range');
  return response.data;
};

export interface DistributionData {
  field: string;
  bins: number;
  min: number;
  max: number;
  data: Array<{
    bin_start: number;
    bin_end: number;
    count: number;
    label: string;
  }>;
}

export const getDistribution = async (params: {
  field: string;
  bins?: number;
  year?: number;
  month?: number;
}) => {
  const response = await apiClient.get<DistributionData>('/data/distribution', { params });
  return response.data;
};

export interface ScatterData {
  x_field: string;
  y_field: string;
  sample_size: number;
  data: Array<Record<string, number>>;
}

export const getScatterData = async (params: {
  x_field: string;
  y_field: string;
  sample_size?: number;
  year?: number;
  month?: number;
}) => {
  const response = await apiClient.get<ScatterData>('/data/scatter', { params });
  return response.data;
};

export interface PaginatedData {
  data: TripRecord[];
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
}

export const getPaginatedData = async (params: {
  page?: number;
  page_size?: number;
  year?: number;
  month?: number;
  payment_type?: number;
  min_fare?: number;
  max_fare?: number;
  min_distance?: number;
  max_distance?: number;
  min_passengers?: number;
  max_passengers?: number;
  order_by?: string;
  order_direction?: 'asc' | 'desc';
}) => {
  const response = await apiClient.get<PaginatedData>('/data/paginated', { params });
  return response.data;
};
