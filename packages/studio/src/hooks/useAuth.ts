// NeuralSite useAuth Hook
// Authentication hook with user state management

import { useEffect, useCallback } from 'react';
import { useUserStore } from '../stores/userStore';
import { LoginRequest } from '../api/types';

interface UseAuthReturn {
  user: ReturnType<typeof useUserStore>['user'];
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  register: (data: { username: string; password: string; real_name?: string }) => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  clearError: () => void;
}

export function useAuth(): UseAuthReturn {
  const {
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    login: storeLogin,
    logout: storeLogout,
    register: storeRegister,
    fetchCurrentUser: storeFetchCurrentUser,
    clearError,
  } = useUserStore();

  // Check auth on mount
  useEffect(() => {
    if (!isAuthenticated && token) {
      storeFetchCurrentUser();
    }
  }, [isAuthenticated, token, storeFetchCurrentUser]);

  const login = useCallback(
    async (credentials: LoginRequest) => {
      await storeLogin(credentials);
    },
    [storeLogin]
  );

  const logout = useCallback(async () => {
    await storeLogout();
  }, [storeLogout]);

  const register = useCallback(
    async (data: { username: string; password: string; real_name?: string }) => {
      await storeRegister(data);
    },
    [storeRegister]
  );

  const fetchCurrentUser = useCallback(async () => {
    await storeFetchCurrentUser();
  }, [storeFetchCurrentUser]);

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    register,
    fetchCurrentUser,
    clearError,
  };
}

/**
 * Hook to check if user has specific role
 */
export function useHasRole(requiredRoles: string | string[]): boolean {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) return false;

  const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
  return roles.includes(user.role);
}

/**
 * Hook to check if user is admin
 */
export function useIsAdmin(): boolean {
  return useHasRole('admin');
}

/**
 * Hook to check if user can manage issues
 */
export function useCanManageIssues(): boolean {
  return useHasRole(['admin', 'manager', 'engineer']);
}

export default useAuth;
