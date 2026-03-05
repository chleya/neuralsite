// NeuralSite Stations API Endpoints

import apiClient from '../client';
import { 
  Station, 
  StationCreate, 
  StationUpdate, 
  StationListParams, 
  StationListResponse 
} from '../types';

export const stationsApi = {
  /**
   * List stations with filters and pagination
   * GET /api/v1/stations
   */
  list: async (params?: StationListParams): Promise<StationListResponse> => {
    return apiClient.get<StationListResponse>('/stations', params);
  },

  /**
   * Get a single station by ID
   * GET /api/v1/stations/:id
   */
  get: async (stationId: string): Promise<Station> => {
    return apiClient.get<Station>(`/stations/${stationId}`);
  },

  /**
   * Get station by station number (e.g., K0+500)
   * GET /api/v1/stations/by-station
   */
  getByStation: async (station: number, routeId?: string): Promise<Station> => {
    return apiClient.get<Station>('/stations/by-station', { station, route_id: routeId });
  },

  /**
   * Create a new station
   * POST /api/v1/stations
   */
  create: async (data: StationCreate): Promise<Station> => {
    return apiClient.post<Station>('/stations', data);
  },

  /**
   * Batch create stations
   * POST /api/v1/stations/batch
   */
  createBatch: async (stations: StationCreate[]): Promise<Station[]> => {
    return apiClient.post<Station[]>('/stations/batch', { stations });
  },

  /**
   * Update a station
   * PUT /api/v1/stations/:id
   */
  update: async (stationId: string, data: StationUpdate): Promise<Station> => {
    return apiClient.put<Station>(`/stations/${stationId}`, data);
  },

  /**
   * Delete a station
   * DELETE /api/v1/stations/:id
   */
  delete: async (stationId: string): Promise<void> => {
    return apiClient.delete<void>(`/stations/${stationId}`);
  },

  /**
   * Import stations from data
   * POST /api/v1/stations/import
   */
  import: async (data: StationCreate[]): Promise<{ success: number; failed: number; errors: string[] }> => {
    return apiClient.post<{ success: number; failed: number; errors: string[] }>('/stations/import', { stations: data });
  },

  /**
   * Export stations to data
   * GET /api/v1/stations/export
   */
  export: async (params?: StationListParams): Promise<Station[]> => {
    return apiClient.get<Station[]>('/stations/export', params);
  },
};

export default stationsApi;
