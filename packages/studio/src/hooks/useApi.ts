// NeuralSite useApi Hook
// Generic hook for API requests with loading and error states

import { useState, useCallback, useEffect, useRef } from 'react';
import { ApiError } from '../api/types';

interface UseApiOptions<T> {
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: ApiError) => void;
}

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

interface UseApiReturn<T> extends UseApiState<T> {
  execute: (params?: unknown) => Promise<T | null>;
  reset: () => void;
}

export function useApi<T>(
  apiFn: (params?: unknown) => Promise<T>,
  options: UseApiOptions<T> = {}
): UseApiReturn<T> {
  const { immediate = false, onSuccess, onError } = options;

  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: immediate,
    error: null,
  });

  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const execute = useCallback(
    async (params?: unknown): Promise<T | null> => {
      if (!mountedRef.current) return null;

      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const result = await apiFn(params);

        if (!mountedRef.current) return null;

        setState({ data: result, loading: false, error: null });
        onSuccess?.(result);
        return result;
      } catch (error) {
        if (!mountedRef.current) return null;

        const apiError = error as ApiError;
        setState((prev) => ({ ...prev, loading: false, error: apiError }));
        onError?.(apiError);
        return null;
      }
    },
    [apiFn, onSuccess, onError]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  // Execute immediately if immediate option is true
  useEffect(() => {
    if (immediate) {
      execute();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

// ==================== Specialized API Hooks ====================

/**
 * Hook for paginated API requests
 */
export function usePaginatedApi<T>(
  apiFn: (params?: unknown) => Promise<{ data: T[]; total: number; page: number; limit: number }>,
  initialParams?: Record<string, unknown>
) {
  const [params, setParams] = useState<Record<string, unknown>>(initialParams || {});
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);

  const { data, loading, error, execute } = useApi(apiFn);

  const fetchPage = useCallback(
    async (newPage: number, newLimit?: number) => {
      const newParams = {
        ...params,
        page: newPage,
        limit: newLimit || limit,
      };
      setPage(newPage);
      if (newLimit) setLimit(newLimit);
      return execute(newParams);
    },
    [execute, params, limit]
  );

  const refresh = useCallback(() => {
    return fetchPage(page, limit);
  }, [fetchPage, page, limit]);

  const goToNextPage = useCallback(() => {
    return fetchPage(page + 1);
  }, [fetchPage, page]);

  const goToPrevPage = useCallback(() => {
    if (page > 1) {
      return fetchPage(page - 1);
    }
    return Promise.resolve(null);
  }, [fetchPage, page]);

  return {
    data,
    loading,
    error,
    page,
    limit,
    setParams,
    fetchPage,
    refresh,
    goToNextPage,
    goToPrevPage,
    hasMore: data ? data.length > 0 : false,
  };
}

/**
 * Hook for mutations (POST, PUT, DELETE)
 */
export function useMutation<TData, TVariables>(
  mutationFn: (variables: TVariables) => Promise<TData>
) {
  const [state, setState] = useState<{
    data: TData | null;
    loading: boolean;
    error: ApiError | null;
  }>({
    data: null,
    loading: false,
    error: null,
  });

  const mutate = useCallback(
    async (variables: TVariables): Promise<TData | null> => {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const result = await mutationFn(variables);
        setState({ data: result, loading: false, error: null });
        return result;
      } catch (error) {
        const apiError = error as ApiError;
        setState({ data: null, loading: false, error: apiError });
        return null;
      }
    },
    [mutationFn]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    mutate,
    reset,
    isLoading: state.loading,
  };
}

export default useApi;
