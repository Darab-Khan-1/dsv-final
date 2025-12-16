import { apiClient } from '../client';
import type { Hotspot, RoutePair, Cluster, SpatialDensity } from '../types';

export const getPickupHotspots = async (params?: { top_n?: number; min_trips?: number }) => {
  const response = await apiClient.get<{ data: Hotspot[] }>('/geospatial/pickup-hotspots', { params });
  return response.data;
};

export const getDropoffHotspots = async (params?: { top_n?: number; min_trips?: number }) => {
  const response = await apiClient.get<{ data: Hotspot[] }>('/geospatial/dropoff-hotspots', { params });
  return response.data;
};

export const getRoutePairs = async (topN: number = 20) => {
  const response = await apiClient.get<{ data: RoutePair[] }>('/geospatial/route-pairs', { 
    params: { top_n: topN } 
  });
  return response.data;
};

export const getClusters = async (params?: { n_clusters?: number; cluster_type?: string }) => {
  const response = await apiClient.get<{ clusters: Cluster[]; n_clusters: number }>('/geospatial/clusters', { params });
  return response.data;
};

export const getSpatialDensity = async (gridSize: number = 0.01) => {
  const response = await apiClient.get<{ data: SpatialDensity[]; grid_size: number }>('/geospatial/spatial-density', { 
    params: { grid_size: gridSize } 
  });
  return response.data;
};
