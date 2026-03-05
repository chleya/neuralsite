// NeuralSite Photos API Endpoints

import apiClient from '../client';
import { Photo, PhotoCreate, PhotoUpdate, PhotoListParams, PhotoListResponse } from '../types';

export const photosApi = {
  /**
   * List photos with filters and pagination
   * GET /api/v1/photos
   */
  list: async (params?: PhotoListParams): Promise<PhotoListResponse> => {
    return apiClient.get<PhotoListResponse>('/photos', params);
  },

  /**
   * Get a single photo by ID
   * GET /api/v1/photos/:id
   */
  get: async (photoId: string): Promise<Photo> => {
    return apiClient.get<Photo>(`/photos/${photoId}`);
  },

  /**
   * Create a new photo record
   * POST /api/v1/photos
   */
  create: async (data: PhotoCreate): Promise<Photo> => {
    return apiClient.post<Photo>('/photos', data);
  },

  /**
   * Update a photo
   * PUT /api/v1/photos/:id
   */
  update: async (photoId: string, data: PhotoUpdate): Promise<Photo> => {
    return apiClient.put<Photo>(`/photos/${photoId}`, data);
  },

  /**
   * Delete a photo
   * DELETE /api/v1/photos/:id
   */
  delete: async (photoId: string): Promise<void> => {
    return apiClient.delete<void>(`/photos/${photoId}`);
  },

  /**
   * Upload a photo file (single)
   * POST /api/v1/photos/upload
   */
  upload: async (file: File, metadata?: Partial<PhotoCreate>): Promise<Photo> => {
    const formData = new FormData();
    formData.append('file', file);

    if (metadata) {
      Object.entries(metadata).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (typeof value === 'object') {
            formData.append(key, JSON.stringify(value));
          } else {
            formData.append(key, String(value));
          }
        }
      });
    }

    return apiClient.post<Photo>('/photos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * PC端批量上传照片
   * POST /api/v1/photos/upload-batch
   */
  uploadBatch: async (
    files: File[], 
    metadata?: Partial<PhotoCreate>,
    onProgress?: (progress: number) => void
  ): Promise<Photo[]> => {
    const results: Photo[] = [];
    const total = files.length;
    
    for (let i = 0; i < files.length; i++) {
      try {
        const formData = new FormData();
        formData.append('file', files[i]);
        
        if (metadata) {
          Object.entries(metadata).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
              if (typeof value === 'object') {
                formData.append(key, JSON.stringify(value));
              } else {
                formData.append(key, String(value));
              }
            }
          });
        }
        
        const photo = await apiClient.post<Photo>('/photos/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        results.push(photo);
        
        if (onProgress) {
          onProgress(Math.round(((i + 1) / total) * 100));
        }
      } catch (error) {
        console.error(`Failed to upload ${files[i].name}:`, error);
        // Continue with other files
      }
    }
    
    return results;
  },

  /**
   * 验证照片
   * POST /api/v1/photos/:id/verify
   */
  verify: async (photoId: string): Promise<Photo> => {
    return apiClient.post<Photo>(`/photos/${photoId}/verify`);
  },

  /**
   * 根据桩号获取照片
   * GET /api/v1/photos/by-station
   */
  getByStation: async (station: number, projectId?: string): Promise<PhotoListResponse> => {
    return apiClient.get<PhotoListResponse>('/photos/by-station', { station, project_id: projectId });
  },

  /**
   * 批量关联照片到桩号
   * POST /api/v1/photos/batch-station
   */
  batchAssignToStation: async (photoIds: string[], station: number, stationDisplay?: string): Promise<void> => {
    return apiClient.post<void>('/photos/batch-station', { 
      photo_ids: photoIds, 
      station, 
      station_display: stationDisplay 
    });
  },
};

export default photosApi;
