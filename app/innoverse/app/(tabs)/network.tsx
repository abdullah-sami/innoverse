import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');

// Import your optimized API service
import { apiService } from '@/services/optimizedApi';

// Enhanced network monitor with better error handling
const networkMonitor = {
  metrics: [],
  authStatus: null,
  
  // Check authentication status before testing
  async checkAuthStatus() {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const refreshToken = await AsyncStorage.getItem('refresh_token');
      
      this.authStatus = {
        hasAccessToken: !!token,
        hasRefreshToken: !!refreshToken,
        tokenExpired: false,
        lastChecked: new Date().toISOString()
      };

      // Try to validate token with a lightweight request
      if (token) {
        try {
          await apiService.get('/user/api/profile', { 
            cache: false,
            timeout: 5000 
          });
          this.authStatus.tokenValid = true;
        } catch (error) {
          this.authStatus.tokenValid = false;
          this.authStatus.tokenExpired = error.message.includes('401');
        }
      }
      
      return this.authStatus;
    } catch (error) {
      console.error('Auth status check failed:', error);
      this.authStatus = {
        hasAccessToken: false,
        hasRefreshToken: false,
        tokenValid: false,
        error: error.message,
        lastChecked: new Date().toISOString()
      };
      return this.authStatus;
    }
  },

  // Test multiple endpoints with better error handling
  async runComprehensiveTest() {
    const testResults = [];
    
    // Check auth first
    await this.checkAuthStatus();
    
    const testEndpoints = [
      { endpoint: '/api/reels/', method: 'GET', description: 'Reels Data', requiresAuth: false },
      { endpoint: '/api/posts/', method: 'GET', description: 'Posts Data', requiresAuth: false },
      { endpoint: '/user/api/profile', method: 'GET', description: 'Profile Info', requiresAuth: true },
    ];

    for (const test of testEndpoints) {
      // Skip auth-required endpoints if not authenticated
      if (test.requiresAuth && !this.authStatus?.tokenValid) {
        const metric = {
          endpoint: test.endpoint,
          description: test.description,
          responseTime: 0,
          payloadSize: 0,
          requestSize: 0,
          cached: false,
          connectionType: 'skipped',
          timestamp: new Date().toISOString(),
          status: 'skipped',
          error: 'Authentication required but token invalid/missing'
        };
        testResults.push(metric);
        this.metrics.push(metric);
        continue;
      }

      try {
        const startTime = Date.now();
        const result = await apiService.get(test.endpoint, { 
          cache: false, 
          compress: true, 
          minify: true,
          timeout: 10000 // 10 second timeout
        });
        
        const metric = {
          endpoint: test.endpoint,
          description: test.description,
          responseTime: result.metrics?.responseTime || (Date.now() - startTime),
          payloadSize: result.metrics?.payloadSize || 0,
          requestSize: result.metrics?.requestSize || 0,
          cached: result.cached || false,
          connectionType: result.metrics?.isConnected ? 'wifi' : 'cellular',
          timestamp: new Date().toISOString(),
          status: 'success',
          httpStatus: 200
        };
        
        testResults.push(metric);
        this.metrics.push(metric);
      } catch (error) {
        const isAuthError = error.message.includes('401');
        const isTimeoutError = error.message.includes('timeout');
        const isNetworkError = error.message.includes('Network');
        
        const metric = {
          endpoint: test.endpoint,
          description: test.description,
          responseTime: 0,
          payloadSize: 0,
          requestSize: 0,
          cached: false,
          connectionType: 'unknown',
          timestamp: new Date().toISOString(),
          status: 'failed',
          error: error.message,
          errorType: isAuthError ? 'auth' : isTimeoutError ? 'timeout' : isNetworkError ? 'network' : 'unknown',
          httpStatus: isAuthError ? 401 : 0
        };
        
        testResults.push(metric);
        this.metrics.push(metric);
      }
    }

    // Keep only last 50 metrics
    this.metrics = this.metrics.slice(-50);
    
    return testResults;
  },

  // Test batch requests with better error handling
  async testBatchRequests() {
    await this.checkAuthStatus();
    
    // Only include endpoints that don't require auth if not authenticated
    const allRequests = [
      { endpoint: '/api/reels', method: 'GET', requiresAuth: false },
      { endpoint: '/api/posts', method: 'GET', requiresAuth: false },
      { endpoint: '/user/api/profile', method: 'GET', requiresAuth: true }
    ];
    
    const batchRequests = allRequests.filter(req => 
      !req.requiresAuth || this.authStatus?.tokenValid
    );

    if (batchRequests.length === 0) {
      const errorMetric = {
        endpoint: '/batch-test',
        description: 'Batch Request Test',
        responseTime: 0,
        payloadSize: 0,
        requestSize: 0,
        cached: false,
        connectionType: 'batch',
        timestamp: new Date().toISOString(),
        status: 'skipped',
        error: 'No available endpoints (authentication required)'
      };
      
      this.metrics.push(errorMetric);
      return errorMetric;
    }

    try {
      const startTime = Date.now();
      const results = await apiService.batch(batchRequests, {
        compress: true,
        minify: true,
        cache: false,
        timeout: 15000
      });
      
      const totalTime = Date.now() - startTime;
      const successfulResults = results.filter(r => r && !r.error);
      const totalPayload = successfulResults.reduce((sum, result) => 
        sum + (result.metrics?.payloadSize || 0), 0
      );
      
      const batchMetric = {
        endpoint: '/batch-test',
        description: 'Batch Request Test',
        responseTime: totalTime,
        payloadSize: totalPayload,
        requestSize: 0,
        cached: false,
        connectionType: 'batch',
        timestamp: new Date().toISOString(),
        status: successfulResults.length === batchRequests.length ? 'success' : 'partial',
        batchSize: batchRequests.length,
        successCount: successfulResults.length,
        failureCount: batchRequests.length - successfulResults.length
      };
      
      this.metrics.push(batchMetric);
      return batchMetric;
    } catch (error) {
      const errorMetric = {
        endpoint: '/batch-test',
        description: 'Batch Request Test',
        responseTime: 0,
        payloadSize: 0,
        requestSize: 0,
        cached: false,
        connectionType: 'batch',
        timestamp: new Date().toISOString(),
        status: 'failed',
        error: error.message
      };
      
      this.metrics.push(errorMetric);
      return errorMetric;
    }
  },

  // Test paginated requests
  async testPaginatedRequests() {
    try {
      const startTime = Date.now();
      const result = await apiService.getPaginated('/api/reels', 1, 20, true, {
        timeout: 10000
      });
      
      const paginatedMetric = {
        endpoint: '/api/reels',
        description: 'Paginated Request',
        responseTime: result.metrics?.responseTime || (Date.now() - startTime),
        payloadSize: result.metrics?.payloadSize || 0,
        requestSize: result.metrics?.requestSize || 0,
        cached: result.cached || false,
        connectionType: 'paginated',
        timestamp: new Date().toISOString(),
        status: 'success',
        itemCount: result.data?.results?.length || 0
      };
      
      this.metrics.push(paginatedMetric);
      return paginatedMetric;
    } catch (error) {
      const errorMetric = {
        endpoint: '/api/reels',
        description: 'Paginated Request',
        responseTime: 0,
        payloadSize: 0,
        requestSize: 0,
        cached: false,
        connectionType: 'paginated',
        timestamp: new Date().toISOString(),
        status: 'failed',
        error: error.message,
        errorType: error.message.includes('401') ? 'auth' : 'unknown'
      };
      
      this.metrics.push(errorMetric);
      return errorMetric;
    }
  },

  getAnalytics() {
    const successfulMetrics = this.metrics.filter(m => m.status === 'success' && m.responseTime > 0);
    const failedMetrics = this.metrics.filter(m => m.status === 'failed');
    const skippedMetrics = this.metrics.filter(m => m.status === 'skipped');
    
    if (this.metrics.length === 0) {
      return null;
    }

    const totalRequests = this.metrics.length;
    const successfulRequests = successfulMetrics.length;
    const failedRequests = failedMetrics.length;
    const skippedRequests = skippedMetrics.length;
    
    // Error analysis
    const authErrors = failedMetrics.filter(m => m.errorType === 'auth').length;
    const timeoutErrors = failedMetrics.filter(m => m.errorType === 'timeout').length;
    const networkErrors = failedMetrics.filter(m => m.errorType === 'network').length;
    
    const responseTimes = successfulMetrics.map(m => m.responseTime);
    const payloadSizes = successfulMetrics.map(m => m.payloadSize);
    
    const averageResponseTime = responseTimes.length > 0 ? 
      responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length : 0;
    const averagePayloadSize = payloadSizes.length > 0 ? 
      payloadSizes.reduce((a, b) => a + b, 0) / payloadSizes.length : 0;
    const slowestRequest = responseTimes.length > 0 ? Math.max(...responseTimes) : 0;
    const largestPayload = payloadSizes.length > 0 ? Math.max(...payloadSizes) : 0;
    
    // Calculate bandwidth estimation (payload size / response time)
    const averageBandwidth = averagePayloadSize > 0 && averageResponseTime > 0 ? 
      (averagePayloadSize * 8) / (averageResponseTime * 1000) : 0; // Mbps

    return {
      totalRequests,
      successfulRequests,
      failedRequests,
      skippedRequests,
      successRate: totalRequests > 0 ? (successfulRequests / totalRequests) * 100 : 0,
      averageResponseTime: Math.round(averageResponseTime),
      averagePayloadSize: Math.round(averagePayloadSize),
      averageBandwidth: averageBandwidth.toFixed(2),
      slowestRequest,
      largestPayload,
      authErrors,
      timeoutErrors,
      networkErrors,
      authStatus: this.authStatus,
      metrics: this.metrics.slice(-10), // Last 10 requests
      cacheStats: apiService.getCacheStats?.() || { inMemorySize: 0 }
    };
  },

  clearMetrics() {
    this.metrics = [];
    this.authStatus = null;
    apiService.clearCache?.();
  }
};

const NetworkDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [networkInfo, setNetworkInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastTestTime, setLastTestTime] = useState(null);
  const [testResults, setTestResults] = useState([]);
  const [authStatus, setAuthStatus] = useState(null);

  useEffect(() => {
    initializeDashboard();
  }, []);

  const initializeDashboard = async () => {
    setIsLoading(true);
    try {
      // Check authentication status
      const authInfo = await networkMonitor.checkAuthStatus();
      setAuthStatus(authInfo);
      
      setNetworkInfo({
        type: 'api',
        isConnected: authInfo.hasAccessToken,
        isInternetReachable: true,
        details: { 
          hasAuth: authInfo.hasAccessToken,
          tokenValid: authInfo.tokenValid,
          baseUrl: apiService.baseUrl || 'Not configured'
        }
      });

      // Load any existing analytics
      loadAnalytics();
    } catch (error) {
      console.error('Failed to initialize dashboard:', error);
      Alert.alert('Error', 'Failed to initialize network dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  const loadAnalytics = () => {
    const data = networkMonitor.getAnalytics();
    setAnalytics(data);
  };

  const runComprehensiveTest = async () => {
    setIsLoading(true);
    setLastTestTime(new Date().toLocaleTimeString());
    
    try {
      // Check auth first
      const authInfo = await networkMonitor.checkAuthStatus();
      setAuthStatus(authInfo);
      
      if (!authInfo.hasAccessToken) {
        Alert.alert(
          'Authentication Required',
          'Some tests will be skipped because no authentication token is available. Please log in first.',
          [
            { text: 'Continue Anyway', onPress: () => proceedWithTests() },
            { text: 'Cancel', style: 'cancel' }
          ]
        );
        return;
      }
      
      if (authInfo.hasAccessToken && !authInfo.tokenValid) {
        Alert.alert(
          'Token Issues Detected',
          'Your authentication token appears to be invalid or expired. Some tests may fail.',
          [
            { text: 'Continue Anyway', onPress: () => proceedWithTests() },
            { text: 'Cancel', style: 'cancel' }
          ]
        );
        return;
      }
      
      await proceedWithTests();
      
    } catch (error) {
      console.error('Network test failed:', error);
      Alert.alert('Test Failed', `Network test encountered an error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const proceedWithTests = async () => {
    Alert.alert('Network Test Started', 'Running comprehensive network tests...');
    
    // Run comprehensive API tests
    const comprehensiveResults = await networkMonitor.runComprehensiveTest();
    
    // Test batch requests
    const batchResult = await networkMonitor.testBatchRequests();
    
    // Test paginated requests
    const paginatedResult = await networkMonitor.testPaginatedRequests();
    
    const allResults = [...comprehensiveResults, batchResult, paginatedResult];
    setTestResults(allResults);
    
    // Update analytics
    loadAnalytics();
    
    // Show results
    const successCount = allResults.filter(r => r.status === 'success').length;
    const failedCount = allResults.filter(r => r.status === 'failed').length;
    const skippedCount = allResults.filter(r => r.status === 'skipped').length;
    const successfulResults = allResults.filter(r => r.status === 'success');
    const avgResponseTime = successfulResults.length > 0 ? 
      successfulResults.reduce((sum, r) => sum + r.responseTime, 0) / successfulResults.length : 0;
    
    let resultMessage = `✅ ${successCount} successful\n❌ ${failedCount} failed\n⏭️ ${skippedCount} skipped`;
    
    if (successfulResults.length > 0) {
      resultMessage += `\n⏱️ Average Response: ${Math.round(avgResponseTime)}ms`;
    }
    
    if (failedCount > 0) {
      const authErrorCount = allResults.filter(r => r.errorType === 'auth').length;
      if (authErrorCount > 0) {
        resultMessage += `\n🔒 ${authErrorCount} authentication errors`;
      }
    }
    
    Alert.alert('Network Test Complete', resultMessage);
  };

  const testSpecificEndpoint = async () => {
    Alert.alert(
      'Test Endpoint',
      'Choose an endpoint to test:',
      [
        { text: 'Reels (No Auth)', onPress: () => testEndpoint('/api/reels', 'Reels') },
        { text: 'Posts (No Auth)', onPress: () => testEndpoint('/api/posts', 'Posts') },
        { text: 'Profile (Auth Required)', onPress: () => testEndpoint('/user/api/profile', 'Profile') },
        { text: 'Cancel', style: 'cancel' }
      ]
    );
  };

  const testEndpoint = async (endpoint, name) => {
    setIsLoading(true);
    try {
      const startTime = Date.now();
      const result = await apiService.get(endpoint, { 
        cache: false, 
        compress: true,
        timeout: 10000
      });
      const endTime = Date.now();
      
      Alert.alert(
        `${name} Test Results`,
        `⏱️ Response Time: ${result.metrics?.responseTime || (endTime - startTime)}ms\n` +
        `📦 Payload Size: ${((result.metrics?.payloadSize || 0) / 1024).toFixed(2)}KB\n` +
        `💾 Cached: ${result.cached ? 'Yes' : 'No'}\n` +
        `✅ Status: Success`
      );
      
      loadAnalytics();
    } catch (error) {
      const isAuthError = error.message.includes('401');
      Alert.alert(
        'Test Failed', 
        `${name} test failed: ${error.message}` +
        (isAuthError ? '\n\n💡 This might be an authentication issue. Please check your login status.' : '')
      );
    } finally {
      setIsLoading(false);
    }
  };

  const clearData = async () => {
    Alert.alert(
      'Clear Data',
      'This will clear all metrics and cache data. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Clear', 
          style: 'destructive',
          onPress: async () => {
            networkMonitor.clearMetrics();
            await apiService.clearCache?.();
            setAnalytics(null);
            setTestResults([]);
            setAuthStatus(null);
            Alert.alert('Success', 'All data cleared');
          }
        }
      ]
    );
  };

  const refreshAuthStatus = async () => {
    setIsLoading(true);
    try {
      const authInfo = await networkMonitor.checkAuthStatus();
      setAuthStatus(authInfo);
      
      // Update network info
      setNetworkInfo(prev => ({
        ...prev,
        isConnected: authInfo.hasAccessToken,
        details: {
          ...prev.details,
          hasAuth: authInfo.hasAccessToken,
          tokenValid: authInfo.tokenValid
        }
      }));
      
      Alert.alert(
        'Auth Status Updated',
        `Token Status: ${authInfo.tokenValid ? 'Valid ✅' : 'Invalid ❌'}\n` +
        `Access Token: ${authInfo.hasAccessToken ? 'Present ✅' : 'Missing ❌'}\n` +
        `Refresh Token: ${authInfo.hasRefreshToken ? 'Present ✅' : 'Missing ❌'}`
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to check authentication status');
    } finally {
      setIsLoading(false);
    }
  };

  const MetricCard = ({ title, value, unit, status, subtitle }) => (
    <View style={[styles.metricCard, { width: (width - 48) / 2 }]}>
      <Text style={styles.metricTitle}>{title}</Text>
      <View style={styles.metricContent}>
        <Text style={styles.metricValue}>{value}{unit}</Text>
        <View style={[
          styles.statusIndicator,
          { backgroundColor: status === 'good' ? '#10B981' : status === 'warning' ? '#F59E0B' : '#EF4444' }
        ]} />
      </View>
      {subtitle && <Text style={styles.metricSubtitle}>{subtitle}</Text>}
    </View>
  );

  const getResponseTimeStatus = (time) => {
    if (time < 500) return 'good';
    if (time < 1000) return 'warning';
    return 'poor';
  };

  const getPayloadStatus = (size) => {
    if (size < 50000) return 'good'; // < 50KB
    if (size < 200000) return 'warning'; // < 200KB
    return 'poor';
  };

  const getSuccessRateStatus = (rate) => {
    if (rate >= 95) return 'good';
    if (rate >= 80) return 'warning';
    return 'poor';
  };

  if (isLoading && !analytics) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Initializing Network Dashboard...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <Text style={styles.title}>Network Performance Dashboard</Text>
      {lastTestTime && (
        <Text style={styles.lastTestTime}>Last Test: {lastTestTime}</Text>
      )}

      {/* Authentication Status Card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>🔐 Authentication Status</Text>
        {authStatus && (
          <View style={styles.cardContent}>
            <Text style={styles.infoText}>
              Access Token: {authStatus.hasAccessToken ? '✅ Present' : '❌ Missing'}
            </Text>
            <Text style={styles.infoText}>
              Token Valid: {authStatus.tokenValid ? '✅ Valid' : '❌ Invalid'}
            </Text>
            <Text style={styles.infoText}>
              Refresh Token: {authStatus.hasRefreshToken ? '✅ Present' : '❌ Missing'}
            </Text>
            {authStatus.error && (
              <Text style={[styles.infoText, { color: '#EF4444' }]}>
                Error: {authStatus.error}
              </Text>
            )}
          </View>
        )}
        <TouchableOpacity 
          style={[styles.testButton, styles.secondaryButton, { marginTop: 8 }]}
          onPress={refreshAuthStatus}
          disabled={isLoading}
        >
          <Text style={[styles.buttonText, { color: '#3B82F6' }]}>
            Refresh Auth Status
          </Text>
        </TouchableOpacity>
      </View>

      {/* API Connection Status */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>🌐 API Connection Status</Text>
        {networkInfo && (
          <View style={styles.cardContent}>
            <Text style={styles.infoText}>Type: {networkInfo.type}</Text>
            <Text style={styles.infoText}>
              Authentication: {networkInfo.details?.hasAuth ? '🟢 Authenticated' : '🔴 Not Authenticated'}
            </Text>
            <Text style={styles.infoText}>
              Token Valid: {networkInfo.details?.tokenValid ? '🟢 Valid' : '🔴 Invalid'}
            </Text>
            <Text style={styles.infoText}>
              Base URL: {networkInfo.details?.baseUrl || 'Not available'}
            </Text>
            <Text style={styles.infoText}>
              Cache Status: {analytics?.cacheStats ? `${analytics.cacheStats.inMemorySize} entries` : 'Empty'}
            </Text>
          </View>
        )}
      </View>

      {/* Test Controls */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>🧪 Network Testing</Text>
        <View style={styles.testControls}>
          <TouchableOpacity 
            style={[styles.testButton, styles.primaryButton]}
            onPress={runComprehensiveTest}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.buttonText}>Run Full Test</Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.testButton, styles.secondaryButton]}
            onPress={testSpecificEndpoint}
            disabled={isLoading}
          >
            <Text style={[styles.buttonText, { color: '#3B82F6' }]}>Test Endpoint</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Performance Analytics */}
      {analytics && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>📊 API Performance Analytics</Text>
          <View style={styles.metricsGrid}>
            <MetricCard 
              title="Success Rate" 
              value={Math.round(analytics.successRate)} 
              unit="%" 
              status={getSuccessRateStatus(analytics.successRate)}
              subtitle={`${analytics.successfulRequests}/${analytics.totalRequests} requests`}
            />
            <MetricCard 
              title="Avg Response" 
              value={analytics.averageResponseTime} 
              unit="ms" 
              status={getResponseTimeStatus(analytics.averageResponseTime)}
            />
            <MetricCard 
              title="Avg Payload" 
              value={Math.round(analytics.averagePayloadSize / 1024)} 
              unit="KB" 
              status={getPayloadStatus(analytics.averagePayloadSize)}
            />
            <MetricCard 
              title="Bandwidth" 
              value={analytics.averageBandwidth} 
              unit=" Mbps" 
              status="good"
            />
          </View>

          <View style={styles.summarySection}>
            <Text style={styles.summaryTitle}>Error Analysis</Text>
            {analytics.authErrors > 0 && (
              <Text style={styles.summaryText}>🔒 Auth Errors: {analytics.authErrors}</Text>
            )}
            {analytics.timeoutErrors > 0 && (
              <Text style={styles.summaryText}>⏰ Timeout Errors: {analytics.timeoutErrors}</Text>
            )}
            {analytics.networkErrors > 0 && (
              <Text style={styles.summaryText}>🌐 Network Errors: {analytics.networkErrors}</Text>
            )}
            {analytics.skippedRequests > 0 && (
              <Text style={styles.summaryText}>⏭️ Skipped Requests: {analytics.skippedRequests}</Text>
            )}
            <Text style={styles.summaryText}>Slowest Request: {analytics.slowestRequest || 0}ms</Text>
            <Text style={styles.summaryText}>Largest Payload: {Math.round((analytics.largestPayload || 0) / 1024)}KB</Text>
            <Text style={styles.summaryText}>Cache Entries: {analytics.cacheStats?.inMemorySize || 0}</Text>
          </View>
        </View>
      )}

      {/* Recent API Requests */}
      {analytics?.metrics && analytics.metrics.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>📝 Recent API Requests</Text>
          {analytics.metrics.slice(-5).map((metric, index) => (
            <View key={index} style={styles.requestItem}>
              <View style={styles.requestInfo}>
                <Text style={styles.requestEndpoint}>{metric.endpoint}</Text>
                <Text style={styles.requestDescription}>{metric.description}</Text>
                <Text style={styles.requestDetails}>
                  {metric.responseTime}ms • {Math.round(metric.payloadSize / 1024)}KB
                  {metric.cached && ' • Cached'}
                  {metric.status === 'failed' && ` • ${metric.errorType || 'Failed'}`}
                  {metric.status === 'skipped' && ' • Skipped'}
                </Text>
              </View>
              <View style={[
                styles.requestStatusIndicator,
                { 
                  backgroundColor: metric.status === 'success' ? '#10B981' : 
                                   metric.status === 'skipped' ? '#6B7280' : '#EF4444' 
                }
              ]} />
            </View>
          ))}
        </View>
      )}

      {/* API Optimization Tips */}
      <View style={styles.tipsCard}>
        <Text style={styles.tipsTitle}>🚀 API Optimization Tips</Text>
        <View style={styles.tipsContent}>
          <Text style={styles.tipText}>• Ensure valid authentication tokens before making requests</Text>
          <Text style={styles.tipText}>• Enable response compression (gzip/br)</Text>
          <Text style={styles.tipText}>• Use request caching for static data</Text>
          <Text style={styles.tipText}>• Implement payload minification</Text>
          <Text style={styles.tipText}>• Set appropriate request timeouts</Text>
          <Text style={styles.tipText}>• Handle authentication errors gracefully</Text>
          <Text style={styles.tipText}>• Monitor cache hit rates</Text>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actionsContainer}>
        <TouchableOpacity 
          style={[styles.actionButton, styles.refreshButton]}
          onPress={loadAnalytics}
          disabled={isLoading}
        >
          <Text style={styles.actionButtonText}>Refresh Data</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.actionButton, styles.clearButton]}
          onPress={clearData}
          disabled={isLoading}
        >
          <Text style={styles.actionButtonText}>Clear Data</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 32,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  lastTestTime: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 24,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  cardContent: {
    marginTop: 8,
  },
  infoText: {
    color: '#374151',
    marginBottom: 4,
    fontSize: 14,
  },
  testControls: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  testButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 44,
  },
  primaryButton: {
    backgroundColor: '#3B82F6',
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#3B82F6',
  },
  buttonText: {
    color: '#FFFFFF',
    fontWeight: '500',
    fontSize: 14,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 8,
    marginBottom: 16,
  },
  metricCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 16,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  metricTitle: {
    fontSize: 12,
    fontWeight: '500',
    color: '#6B7280',
    marginBottom: 4,
  },
  metricContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
  },
  metricSubtitle: {
    fontSize: 10,
    color: '#9CA3AF',
    marginTop: 2,
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  summarySection: {
    marginTop: 16,
  },
  summaryTitle: {
    fontSize: 12,
    fontWeight: '500',
    color: '#6B7280',
    marginBottom: 8,
  },
  summaryText: {
    color: '#374151',
    marginBottom: 4,
    fontSize: 14,
  },
  requestItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  requestInfo: {
    flex: 1,
  },
  requestEndpoint: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
  },
  requestDescription: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  requestDetails: {
    fontSize: 11,
    color: '#9CA3AF',
    marginTop: 2,
  },
  requestStatusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginLeft: 8,
  },
  tipsCard: {
    backgroundColor: '#EFF6FF',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  tipsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1E3A8A',
    marginBottom: 8,
  },
  tipsContent: {
    gap: 4,
  },
  tipText: {
    color: '#1E40AF',
    fontSize: 14,
    lineHeight: 20,
  },
  actionsContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
  },
  refreshButton: {
    backgroundColor: '#10B981',
  },
  clearButton: {
    backgroundColor: '#EF4444',
  },
  actionButtonText: {
    color: '#FFFFFF',
    fontWeight: '500',
    fontSize: 16,
  },
});

export default NetworkDashboard; 