// NeuralSite Auth API Endpoints

import apiClient from '../client';
import { LoginRequest, LoginResponse, RegisterRequest, User } from '../types';

export const authApi = {
  /**
   * User login
   * POST /api/v1/auth/login
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    return apiClient.post<LoginResponse>('/auth/login', credentials);
  },

  /**
   * User registration
   * POST /api/v1/auth/register
   */
  register: async (data: RegisterRequest): Promise<User> => {
    return apiClient.post<User>('/auth/register', data);
  },

  /**
   * Refresh access token
   * POST /api/v1/auth/refresh
   */
  refreshToken: async (): Promise<LoginResponse> => {
    return apiClient.post<LoginResponse>('/auth/refresh');
  },

  /**
   * User logout
   * POST /api/v1/auth/logout
   */
  logout: async (): Promise<void> => {
    return apiClient.post<void>('/auth/logout');
  },

  /**
   * Get current user info
   * GET /api/v1/auth/me
   */
  getCurrentUser: async (): Promise<User> => {
    return apiClient.get<User>('/auth/me');
  },

  /**
   * Change password
   * PUT /api/v1/auth/me/password
   */
  changePassword: async (oldPassword: string, newPassword: string): Promise<void> => {
    return apiClient.put<void>('/auth/me/password', { old_password: oldPassword, new_password: newPassword });
  },
};

export default authApi;
