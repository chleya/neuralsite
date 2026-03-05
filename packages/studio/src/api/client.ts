import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { create } from 'zustand';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export interface User {
  id: number;
  username: string;
  email: string;
}

export interface AuthState {
  token: string | null;
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('token'),
  user: null,
  isLoading: false,
  login: async (username: string, password: string) => {
    set({ isLoading: true });
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/login`, {
        username,
        password,
      });
      const { token, user } = response.data;
      localStorage.setItem('token', token);
      set({ token, user, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
  logout: () => {
    localStorage.removeItem('token');
    set({ token: null, user: null });
  },
}));

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('token');
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
    const response = await this.client.get<T>(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.client.post<T>(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.client.put<T>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url);
    return response.data;
  }
}

export const apiClient = new ApiClient();

export interface Photo {
  id: number;
  filename: string;
  url: string;
  thumbnail_url: string;
  width: number;
  height: number;
  file_size: number;
  captured_at: string;
  location?: string;
  tags: string[];
}

export interface Issue {
  id: number;
  title: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  photos: Photo[];
  created_at: string;
  updated_at: string;
}

export const photoApi = {
  list: (params?: { page?: number; limit?: number; search?: string }) =>
    apiClient.get<{ photos: Photo[]; total: number }>('/photos', params),
  get: (id: number) => apiClient.get<Photo>(`/photos/${id}`),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('photo', file);
    return apiClient.post<Photo>('/photos', formData);
  },
  delete: (id: number) => apiClient.delete(`/photos/${id}`),
};

export const issueApi = {
  list: (params?: { status?: string; priority?: string; page?: number; limit?: number }) =>
    apiClient.get<{ issues: Issue[]; total: number }>('/issues', params),
  get: (id: number) => apiClient.get<Issue>(`/issues/${id}`),
  create: (data: { title: string; description: string; priority: string; photo_ids?: number[] }) =>
    apiClient.post<Issue>('/issues', data),
  update: (id: number, data: Partial<Issue>) => apiClient.put<Issue>(`/issues/${id}`, data),
  delete: (id: number) => apiClient.delete(`/issues/${id}`),
};
