// services/networkMonitor.ts
import NetInfo from '@react-native-community/netinfo';

export interface NetworkMetrics {
  responseTime: number;
  payloadSize: number;
  requestSize: number;
  networkSpeed?: string;
  connectionType?: string;
  isConnected: boolean;
  bandwidth?: number;
}

export interface RequestTimings {
  startTime: number;
  endTime: number;
  duration: number;
  dnsLookup?: number;
  tcpConnect?: number;
  tlsHandshake?: number;
  firstByte?: number;
}

class NetworkPerformanceMonitor {
  private static instance: NetworkPerformanceMonitor;
  private metrics: NetworkMetrics[] = [];

  public static getInstance(): NetworkPerformanceMonitor {
    if (!NetworkPerformanceMonitor.instance) {
      NetworkPerformanceMonitor.instance = new NetworkPerformanceMonitor();
    }
    return NetworkPerformanceMonitor.instance;
  }

  // Enhanced fetch wrapper with detailed metrics
  async monitoredFetch(
    url: string, 
    options: RequestInit = {},
    label?: string
  ): Promise<{ response: Response; metrics: NetworkMetrics; timings: RequestTimings }> {
    const startTime = performance.now();
    const requestStart = Date.now();

    // Get network info
    const netInfo = await NetInfo.fetch();
    
    // Calculate request payload size
    const requestSize = this.calculateRequestSize(options);
    
    console.log(`🚀 [${label || 'Request'}] Starting request to ${url}`);
    console.log(`📊 Request size: ${this.formatBytes(requestSize)}`);
    console.log(`🌐 Connection: ${netInfo.type} - ${netInfo.isConnected ? 'Connected' : 'Disconnected'}`);
 
    try {
      // Make the actual request
      const response = await fetch(url, {
        ...options,
        // Add timing headers if server supports them
        headers: {
          ...options.headers,
          'X-Request-Start': requestStart.toString(),
        }
      });

      const endTime = performance.now();
      const responseTime = endTime - startTime;

      // Calculate response payload size
      const responseClone = response.clone();
      const responseText = await responseClone.text();
      const payloadSize = new Blob([responseText]).size;

      // Create metrics object
      const metrics: NetworkMetrics = {
        responseTime: Math.round(responseTime),
        payloadSize,
        requestSize,
        networkSpeed: netInfo.details?.effectiveType || 'unknown',
        connectionType: netInfo.type || 'unknown',
        isConnected: netInfo.isConnected || false,
        bandwidth: this.estimateBandwidth(payloadSize, responseTime),
      };

      const timings: RequestTimings = {
        startTime,
        endTime,
        duration: responseTime,
        // Note: Detailed timing breakdown requires server support or browser APIs
      };

      // Store metrics for analysis
      this.metrics.push(metrics);

      // Log performance metrics
      this.logMetrics(label || 'Request', metrics, url);

      return { response, metrics, timings };

    } catch (error) {
      const endTime = performance.now();
      const responseTime = endTime - startTime;
      
      console.error(`❌ [${label || 'Request'}] Failed after ${responseTime.toFixed(2)}ms:`, error);
      throw error;
    }
  }

  // Calculate request payload size
  private calculateRequestSize(options: RequestInit): number {
    let size = 0;
    
    // Headers size estimation
    if (options.headers) {
      const headers = new Headers(options.headers);
      headers.forEach((value, key) => {
        size += key.length + value.length + 4; // +4 for ': ' and '\r\n'
      });
    }

    // Body size
    if (options.body) {
      if (typeof options.body === 'string') {
        size += new Blob([options.body]).size;
      } else if (options.body instanceof FormData) {
        // FormData size estimation is approximate
        size += 1000; // Rough estimate
      } else if (options.body instanceof URLSearchParams) {
        size += options.body.toString().length;
      }
    }

    return size;
  }

  // Estimate bandwidth in Mbps
  private estimateBandwidth(bytes: number, timeMs: number): number {
    const bitsPerSecond = (bytes * 8) / (timeMs / 1000);
    return Math.round((bitsPerSecond / 1000000) * 100) / 100; // Convert to Mbps
  }

  // Format bytes to human readable format
  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`;
  }

  // Enhanced logging with performance indicators
  private logMetrics(label: string, metrics: NetworkMetrics, url: string) {
    const { responseTime, payloadSize, requestSize, bandwidth, connectionType } = metrics;
    
    // Performance thresholds
    const isSlowResponse = responseTime > 1000; // > 1 second
    const isLargePayload = payloadSize > 100000; // > 100KB
    const isSlowConnection = (bandwidth || 0) < 1; // < 1 Mbps

    console.log(`\n📈 [${label}] Performance Report:`);
    console.log(`🕐 Response Time: ${responseTime}ms ${isSlowResponse ? '⚠️  SLOW' : '✅'}`);
    console.log(`📦 Response Size: ${this.formatBytes(payloadSize)} ${isLargePayload ? '⚠️  LARGE' : '✅'}`);
    console.log(`📤 Request Size: ${this.formatBytes(requestSize)}`);
    console.log(`🌐 Connection: ${connectionType}`);
    console.log(`⚡ Bandwidth: ${bandwidth} Mbps ${isSlowConnection ? '⚠️  SLOW' : '✅'}`);
    console.log(`🎯 URL: ${url}`);
    
    if (isSlowResponse || isLargePayload || isSlowConnection) {
      console.log(`\n💡 Optimization Suggestions:`);
      if (isSlowResponse) console.log(`   • Consider request caching or pagination`);
      if (isLargePayload) console.log(`   • Implement response compression or reduce payload`);
      if (isSlowConnection) console.log(`   • Optimize for low bandwidth scenarios`);
    }
    console.log(`─────────────────────────────────────────────`);
  }

  // Get performance analytics
  getAnalytics() {
    if (this.metrics.length === 0) return null;

    const avgResponseTime = this.metrics.reduce((sum, m) => sum + m.responseTime, 0) / this.metrics.length;
    const avgPayloadSize = this.metrics.reduce((sum, m) => sum + m.payloadSize, 0) / this.metrics.length;
    const avgBandwidth = this.metrics.reduce((sum, m) => sum + (m.bandwidth || 0), 0) / this.metrics.length;

    return {
      totalRequests: this.metrics.length,
      averageResponseTime: Math.round(avgResponseTime),
      averagePayloadSize: Math.round(avgPayloadSize),
      averageBandwidth: Math.round(avgBandwidth * 100) / 100,
      slowestRequest: Math.max(...this.metrics.map(m => m.responseTime)),
      largestPayload: Math.max(...this.metrics.map(m => m.payloadSize)),
      metrics: this.metrics.slice(-10) // Last 10 requests
    };
  }

  // Clear stored metrics
  clearMetrics() {
    this.metrics = [];
  }

  // Real-time network monitoring
  async startNetworkMonitoring(callback: (info: any) => void) {
    const unsubscribe = NetInfo.addEventListener(state => {
      callback({
        type: state.type,
        isConnected: state.isConnected,
        isInternetReachable: state.isInternetReachable,
        details: state.details
      });
    });

    return unsubscribe;
  }

  // Test network speed with a small request
  async testNetworkSpeed(testUrl?: string): Promise<{ downloadSpeed: number; latency: number }> {
    const url = testUrl || 'https://httpbin.org/bytes/1024'; // 1KB test
    const startTime = performance.now();
    
    try {
      const response = await fetch(url);
      const endTime = performance.now();
      const responseTime = endTime - startTime;
      
      if (response.ok) {
        const data = await response.blob();
        const downloadSpeed = (data.size * 8) / (responseTime / 1000) / 1000000; // Mbps
        
        return {
          downloadSpeed: Math.round(downloadSpeed * 100) / 100,
          latency: Math.round(responseTime)
        };
      }
      throw new Error('Speed test failed');
    } catch (error) {
      console.error('Network speed test failed:', error);
      return { downloadSpeed: 0, latency: 0 };
    }
  }
}

export const networkMonitor = NetworkPerformanceMonitor.getInstance();