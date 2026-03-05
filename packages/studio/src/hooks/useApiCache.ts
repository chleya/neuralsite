import { useState, useEffect, useRef, useCallback } from 'react'

interface CacheItem<T> {
  data: T
  timestamp: number
}

interface UseApiCacheOptions<T> {
  key: string
  fetchFn: () => Promise<T>
  ttl?: number // 缓存有效期（毫秒）
  enabled?: boolean
}

// 内存缓存
const memoryCache = new Map<string, CacheItem<any>>()

// 清理过期缓存
function cleanExpiredCache(maxAge: number = 5 * 60 * 1000) { // 默认5分钟
  const now = Date.now()
  for (const [key, item] of memoryCache.entries()) {
    if (now - item.timestamp > maxAge) {
      memoryCache.delete(key)
    }
  }
}

// 定期清理
setInterval(() => cleanExpiredCache(), 60 * 1000)

export function useApiCache<T>({
  key,
  fetchFn,
  ttl = 5 * 60 * 1000, // 默认5分钟缓存
  enabled = true
}: UseApiCacheOptions<T>) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const fetchData = useCallback(async (forceRefresh = false) => {
    // 检查缓存
    if (!forceRefresh && memoryCache.has(key)) {
      const cached = memoryCache.get(key)!
      if (Date.now() - cached.timestamp < ttl) {
        setData(cached.data)
        return cached.data
      }
    }

    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    setLoading(true)
    setError(null)

    try {
      const result = await fetchFn()
      
      // 存入缓存
      memoryCache.set(key, {
        data: result,
        timestamp: Date.now()
      })
      
      setData(result)
      return result
    } catch (err: any) {
      if (err.name !== 'CanceledError' && err.name !== 'AbortError') {
        setError(err.message || '请求失败')
        throw err
      }
    } finally {
      setLoading(false)
    }
  }, [key, fetchFn, ttl])

  // 初始加载
  useEffect(() => {
    if (enabled) {
      fetchData()
    }
  }, [enabled])

  // 刷新
  const refresh = useCallback(() => fetchData(true), [fetchData])

  // 清除缓存
  const clearCache = useCallback(() => {
    memoryCache.delete(key)
    setData(null)
  }, [key])

  return {
    data,
    loading,
    error,
    refresh,
    clearCache,
    isCached: memoryCache.has(key)
  }
}

// 预设的缓存Hook
export function useStationQuery(station: string, routeId?: string) {
  return useApiCache({
    key: `station:${routeId || 'default'}:${station}`,
    fetchFn: async () => {
      const { queryStation } = await import('../services/api')
      return queryStation({ station, route_id: routeId })
    },
    enabled: !!station
  })
}

export function usePhotos(routeId?: string, station?: string) {
  return useApiCache({
    key: `photos:${routeId || 'all'}:${station || 'all'}`,
    fetchFn: async () => {
      const { queryPhotos } = await import('../services/api')
      return queryPhotos({ route_id: routeId, station })
    },
    ttl: 10 * 60 * 1000 // 照片缓存10分钟
  })
}

export function useModels() {
  return useApiCache({
    key: 'models:list',
    fetchFn: async () => {
      const { listModels } = await import('../services/api')
      return listModels()
    },
    ttl: 30 * 60 * 1000 // 模型列表缓存30分钟
  })
}

export default useApiCache
