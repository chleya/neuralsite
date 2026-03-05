// NeuralSite User Store
// Zustand store for user authentication state

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, LoginRequest } from '../api/types';
import { authApi } from '../api/endpoints';

interface AuthState {
  // State
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  register: (data: { username: string; password: string; real_name?: string }) => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  clearError: () => void;
}

export const useUserStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Login action
      login: async (credentials: LoginRequest) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.login(credentials);
          const { access_token, ...userData } = response;

          localStorage.setItem('access_token', access_token);

          set({
            token: access_token,
            user: userData as unknown as User,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : 'Login failed';
          set({
            isLoading: false,
            error: message,
          });
          throw error;
        }
      },

      // Logout action
      logout: async () => {
        try {
          await authApi.logout();
        } catch {
          // Ignore logout API errors
        } finally {
          localStorage.removeItem('access_token');
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            error: null,
          });
        }
      },

      // Register action
      register: async (data: { username: string; password: string; real_name?: string }) => {
        set({ isLoading: true, error: null });
        try {
          const user = await authApi.register(data);
          set({
            user,
            isLoading: false,
            error: null,
          });
          // Auto login after registration
          await get().login({ username: data.username, password: data.password });
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : 'Registration failed';
          set({
            isLoading: false,
            error: message,
          });
          throw error;
        }
      },

      // Fetch current user
      fetchCurrentUser: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }

        set({ isLoading: true });
        try {
          const user = await authApi.getCurrentUser();
          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch {
          localStorage.removeItem('access_token');
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },

      // Clear error
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'neuralsite-auth',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export default useUserStore;
