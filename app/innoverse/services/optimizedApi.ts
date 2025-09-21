// services/optimizedApi.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import { networkMonitor, NetworkMetrics } from './networkMonitor';
import { INNOVERSE_API_CONFIG } from './api';

interface ApiResponse<T = any> {
  data: T;
  metrics: NetworkMetrics;
  cached?: boolean;
}

interface RequestConfig {
  compress?: boolean;
  cache?: boolean;
  timeout?: number;
  retries?: number;
  minify?: boolean;
}

class OptimizedApiService {
  private baseUrl: string;
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes default

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  // Optimized GET request
  async get<T>(
    endpoint: string, 
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const cacheKey = `GET:${url}`;

    // Check cache first
    if (config.cache !== false) {
      const cached = await this.getFromCache<T>(cacheKey);
      if (cached) {
        console.log(`💾 Cache hit for ${endpoint}`);
        return { 
          data: cached, 
          metrics: { responseTime: 0, payloadSize: 0, requestSize: 0, isConnected: true },
          cached: true 
        };
      }
    }

    const token = await AsyncStorage.getItem('access_token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (token) {
        console.log(token)
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Add compression headers
    if (config.compress !== false) {
      headers['Accept-Encoding'] = 'gzip, deflate, br';
    }

    // Add minification hint for API
    if (config.minify) {
      headers['X-Minify-Response'] = 'true';
    }

    const { response, metrics } = await networkMonitor.monitoredFetch(
      url,
      {
        method: 'GET',
        headers,
        signal: this.createAbortSignal(config.timeout || 10000),
      },
      `GET ${endpoint}`
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    // Cache successful responses
    if (config.cache !== false && response.status === 200) {
      await this.setCache(cacheKey, data, this.CACHE_TTL);
    }

    return { data, metrics, cached: false };
  }

  // Optimized POST request with payload compression
  async post<T>(
    endpoint: string, 
    payload: any, 
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const token = await AsyncStorage.getItem('access_token');

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (token) {
        console.log(token)
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Optimize payload
    const optimizedPayload = config.minify ? this.minifyPayload(payload) : payload;
    const body = JSON.stringify(optimizedPayload);

    // Add compression headers
    if (config.compress !== false) {
      headers['Accept-Encoding'] = 'gzip, deflate, br';
      headers['Content-Encoding'] = 'gzip'; // If you implement client-side compression
    }

    const { response, metrics } = await networkMonitor.monitoredFetch(
      url,
      {
        method: 'POST',
        headers,
        body,
        signal: this.createAbortSignal(config.timeout || 15000),
      },
      `POST ${endpoint}`
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return { data, metrics, cached: false };
  }

  // Batch multiple requests
  async batch<T>(
    requests: Array<{ endpoint: string; method: 'GET' | 'POST'; payload?: any }>,
    config: RequestConfig = {}
  ): Promise<Array<ApiResponse<T>>> {
    console.log(`🔄 Batching ${requests.length} requests`);
    
    const batchPromises = requests.map(async (req, index) => {
      try {
        if (req.method === 'GET') {
          return await this.get<T>(req.endpoint, config);
        } else {
          return await this.post<T>(req.endpoint, req.payload, config);
        }
      } catch (error) {
        console.error(`❌ Batch request ${index} failed:`, error);
        throw error;
      }
    });

    const results = await Promise.allSettled(batchPromises);
    
    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        console.error(`Batch request ${index} failed:`, result.reason);
        throw result.reason;
      }
    });
  }

  // Paginated requests with prefetching
  async getPaginated<T>(
    endpoint: string,
    page: number = 1,
    pageSize: number = 20,
    prefetchNext: boolean = true
  ): Promise<ApiResponse<{ results: T[]; count: number; next: string | null; previous: string | null }>> {
    const paginatedEndpoint = `${endpoint}?page=${page}&page_size=${pageSize}`;
    const result = await this.get<{ results: T[]; count: number; next: string | null; previous: string | null }>(
      paginatedEndpoint,
      { cache: true, minify: true }
    );

    // Prefetch next page in background
    if (prefetchNext && result.data.next && page === 1) {
      setTimeout(() => {
        this.get<T>(`${endpoint}?page=${page + 1}&page_size=${pageSize}`, { cache: true, minify: true })
          .catch(() => {}); // Silent fail for prefetch
      }, 100);
    }

    return result;
  }

  // Cache management
  private async getFromCache<T>(key: string): Promise<T | null> {
    try {
      // Check in-memory cache first
      const memCached = this.cache.get(key);
      if (memCached && Date.now() - memCached.timestamp < memCached.ttl) {
        return memCached.data;
      }

      // Check AsyncStorage cache
      const cached = await AsyncStorage.getItem(`cache_${key}`);
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Date.now() - parsed.timestamp < parsed.ttl) {
          // Update in-memory cache
          this.cache.set(key, parsed);
          return parsed.data;
        }
        // Remove expired cache
        await AsyncStorage.removeItem(`cache_${key}`);
      }
      
      return null;
    } catch (error) {
      console.error('Cache read error:', error);
      return null;
    }
  }

  private async setCache(key: string, data: any, ttl: number) {
    try {
      const cacheItem = { data, timestamp: Date.now(), ttl };
      
      // Set in-memory cache
      this.cache.set(key, cacheItem);
      
      // Set AsyncStorage cache for persistence
      await AsyncStorage.setItem(`cache_${key}`, JSON.stringify(cacheItem));
    } catch (error) {
      console.error('Cache write error:', error);
    }
  }

  // Minify payload by removing unnecessary whitespace and null values
  private minifyPayload(payload: any): any {
    if (typeof payload !== 'object' || payload === null) {
      return payload;
    }

    if (Array.isArray(payload)) {
      return payload.map(item => this.minifyPayload(item));
    }

    const minified: any = {};
    for (const [key, value] of Object.entries(payload)) {
      if (value !== null && value !== undefined && value !== '') {
        minified[key] = this.minifyPayload(value);
      }
    }
    return minified;
  }

  // Create abort signal with timeout
  private createAbortSignal(timeout: number): AbortSignal {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), timeout);
    return controller.signal;
  }

  // Clear all caches
  async clearCache() {
    this.cache.clear();
    const keys = await AsyncStorage.getAllKeys();
    const cacheKeys = keys.filter(key => key.startsWith('cache_'));
    if (cacheKeys.length > 0) {
      await AsyncStorage.multiRemove(cacheKeys);
    }
    console.log('🧹 All caches cleared');
  }

  // Get cache statistics
  getCacheStats() {
    return {
      inMemorySize: this.cache.size,
      memoryEntries: Array.from(this.cache.keys()),
    };
  }
}

// Enhanced login function using optimized API
export const fetchLogin = async (credentials: { username: string; password: string }) => {
  const apiService = new OptimizedApiService(`${INNOVERSE_API_CONFIG.BASE_URL}/user/login`);
  
  const result = await apiService.post('/auth/login/', credentials, {
    compress: true,
    minify: true,
    timeout: 10000
  });

  console.log(`🔐 Login completed in ${result.metrics.responseTime}ms`);
  console.log(`📦 Response size: ${(result.metrics.payloadSize / 1024).toFixed(2)}KB`);
  
  return result.data;
};

// Create singleton instance
export const apiService = new OptimizedApiService(`${INNOVERSE_API_CONFIG.BASE_URL}`);