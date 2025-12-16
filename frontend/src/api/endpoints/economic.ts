import { apiClient } from '../client';
import type { 
  CorrelationMatrix, 
  TipAnalysis, 
  RevenueData, 
  PriceElasticity,
  SurgePricing,
  CustomerSegment,
  MarketShare,
  EconomicInsights
} from '../types';

export const getCorrelations = async () => {
  const response = await apiClient.get<CorrelationMatrix>('/economic/correlations');
  return response.data;
};

export const getTipAnalysis = async (groupBy: 'payment_type' | 'hour' | 'distance_bucket' | 'location' = 'payment_type') => {
  const response = await apiClient.get<{ data: TipAnalysis[] }>('/economic/tip-analysis', { 
    params: { group_by: groupBy } 
  });
  return response.data;
};

export const getRevenueAnalysis = async (params?: { group_by?: 'hour' | 'location' | 'zone'; year?: number }) => {
  const response = await apiClient.get<{ data: RevenueData[] }>('/economic/revenue-analysis', { params });
  return response.data;
};

export const getPriceElasticity = async () => {
  const response = await apiClient.get<{ data: PriceElasticity[] }>('/economic/price-elasticity');
  return response.data;
};

export const getSurgePricing = async (threshold: number = 3.0) => {
  const response = await apiClient.get<SurgePricing>('/economic/surge-pricing', { 
    params: { threshold } 
  });
  return response.data;
};

export const getCustomerSegments = async (nSegments: number = 5) => {
  const response = await apiClient.get<{ segments: CustomerSegment[]; n_segments: number }>('/economic/customer-segments', { 
    params: { n_segments: nSegments } 
  });
  return response.data;
};

export const getMarketShare = async () => {
  const response = await apiClient.get<{ data: MarketShare[]; total_trips: number }>('/economic/market-share');
  return response.data;
};

export const getEconomicInsights = async () => {
  const response = await apiClient.get<EconomicInsights>('/economic/insights');
  return response.data;
};
