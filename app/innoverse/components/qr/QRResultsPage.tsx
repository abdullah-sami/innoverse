// QRResultsPage.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StatusBar, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { create } from 'twrnc';
import { INNOVERSE_API_CONFIG } from '@/services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const tw = create(require('../../tailwind.twrnc.config.js'));

interface RouteParams {
  page: string;
  segment: string;
  qr_code_data: string;
}

interface EntryResponse {
  success: boolean;
  error?: string[];
}

interface GiftsResponse {
  tshirt?: number;
  breakfast?: number;
  notebook?: number;
  snacks?: number;
  [key: string]: number | undefined;
}

interface GenericResponse {
  allowed: boolean;
  name?: string;
  error?: string;
  [key: string]: any;
}

const GIFT_NAMES = {
  tshirt: 'T-Shirt',
  breakfast: 'Breakfast',
  notebook: 'Notebook',
  snacks: 'Snacks'
};

export const QRResultsPage = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const { page, segment, qr_code_data } = route.params as RouteParams;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [entrySuccess, setEntrySuccess] = useState(false);
  const [gifts, setGifts] = useState<GiftsResponse>({});
  const [genericData, setGenericData] = useState<GenericResponse | null>(null);
  const [updatingGift, setUpdatingGift] = useState<string | null>(null);

  // Helper function to get headers with Authorization token
  const getHeaders = async () => {
    const token = await AsyncStorage.getItem("access_token");
    return {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  };

  // Record Entry API call
  const recordEntry = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const headers = await getHeaders();
      console.log('Entry recording - Headers:', headers);
      console.log('Entry recording - URL:', `${INNOVERSE_API_CONFIG.BASE_URL}/api/recordentry/${qr_code_data}/`);
      
      const response = await fetch(
        `${INNOVERSE_API_CONFIG.BASE_URL}/api/recordentry/${qr_code_data}/`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({}),
        }
      );

      console.log('Entry recording - Response status:', response.status);
      console.log('Entry recording - Response headers:', response.headers);

      // Check if response is actually JSON
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const textResponse = await response.text();
        console.log('Entry recording - Non-JSON response:', textResponse);
        throw new Error('Server returned non-JSON response');
      }

      const data: EntryResponse = await response.json();
      console.log('Entry recording - Response data:', data);
      
      if (response.ok && data.success) {
        setEntrySuccess(true);
      } else {
        setError(data.error ? data.error.join(', ') : 'Failed to record entry');
      }
    } catch (err) {
      console.error('Entry recording error:', err);
      if (err.message.includes('JSON Parse error') || err.message.includes('non-JSON response')) {
        setError('Server error. Please check your connection and try again.');
      } else {
        setError('Network error. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Get Gifts API call
  const getGifts = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const headers = await getHeaders();
      console.log('Gifts - Headers:', headers);
      console.log('Gifts - URL:', `${INNOVERSE_API_CONFIG.BASE_URL}/api/gifts/${qr_code_data}/`);
      
      const response = await fetch(
        `${INNOVERSE_API_CONFIG.BASE_URL}/api/gifts/${qr_code_data}/`,
        {
          method: 'GET',
          headers,
        }
      );

      console.log('Gifts - Response status:', response.status);

      // Check if response is actually JSON
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const textResponse = await response.text();
        console.log('Gifts - Non-JSON response:', textResponse);
        throw new Error('Server returned non-JSON response');
      }

      if (response.ok) {
        const data: GiftsResponse = await response.json();
        console.log('Gifts - Response data:', data);
        setGifts(data);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to fetch gifts');
      }
    } catch (err) {
      console.error('Gifts fetching error:', err);
      if (err.message.includes('JSON Parse error') || err.message.includes('non-JSON response')) {
        setError('Server error. Please check your connection and try again.');
      } else {
        setError('Network error. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Update Gift Status API call
  const updateGiftStatus = async (giftName: string) => {
    setUpdatingGift(giftName);
    
    try {
      const headers = await getHeaders();
      const response = await fetch(
        `${INNOVERSE_API_CONFIG.BASE_URL}/api/gifts/${giftName}/${qr_code_data}/`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({}),
        }
      );

      if (response.ok) {
        // Refresh gifts data
        await getGifts();
      } else {
        const errorData = await response.json();
        Alert.alert('Error', errorData.error || 'Failed to update gift status');
      }
    } catch (err) {
      Alert.alert('Error', 'Network error. Please try again.');
      console.error('Gift update error:', err);
    } finally {
      setUpdatingGift(null);
    }
  };

  // Generic API call for other pages
  const fetchGenericData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const headers = await getHeaders();
      const endpoint = segment 
        ? `${INNOVERSE_API_CONFIG.BASE_URL}/api/${page}/${segment}/${qr_code_data}/`
        : `${INNOVERSE_API_CONFIG.BASE_URL}/api/${page}/${qr_code_data}/`;
      
      console.log('Generic - Headers:', headers);
      console.log('Generic - URL:', endpoint);
      
      const response = await fetch(endpoint, {
        method: 'GET',
        headers,
      });

      console.log('Generic - Response status:', response.status);

      // Check if response is actually JSON
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const textResponse = await response.text();
        console.log('Generic - Non-JSON response:', textResponse);
        throw new Error('Server returned non-JSON response');
      }

      if (response.ok) {
        const data: GenericResponse = await response.json();
        console.log('Generic - Response data:', data);
        setGenericData(data);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Request failed');
      }
    } catch (err) {
      console.error('Generic fetch error:', err);
      if (err.message.includes('JSON Parse error') || err.message.includes('non-JSON response')) {
        setError('Server error. Please check your connection and try again.');
      } else {
        setError('Network error. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Initialize based on page type
  useEffect(() => {
    if (page === 'entry') {
      recordEntry();
    } else if (page === 'gifts') {
      getGifts();
    } else {
      fetchGenericData();
    }
  }, [page, segment, qr_code_data]);

  // Navigation helper
  const openQRScanner = (scanPage: string, scanSegment: string) => {
    navigation.navigate('qr_scanner', { page: scanPage, segment: scanSegment });
  };

  // Get page title
  const getPageTitle = () => {
    if (page === 'entry') return 'Record Entry';
    if (page === 'gifts') return 'Gifts';
    return page.charAt(0).toUpperCase() + page.slice(1);
  };

  // Back button handler
  const handleBack = () => {
    navigation.goBack();
  };

  // Render loading state
  if (loading && page !== 'gifts') {
    return (
      <SafeAreaView style={tw`flex-1 bg-bgPrimary`}>
        <StatusBar backgroundColor="#79BF0D" barStyle="light-content" />
        
        {/* Header */}
        <View style={tw`bg-accentLight px-4 py-3 flex-row items-center`}>
          <TouchableOpacity onPress={handleBack} style={tw`mr-3`}>
            <Text style={tw`text-white text-xl`}>←</Text>
          </TouchableOpacity>
          <Text style={tw`text-white text-lg font-semibold`}>{getPageTitle()}</Text>
        </View>

        <View style={tw`flex-1 justify-center items-center`}>
          <ActivityIndicator size="large" color="#79BF0D" />
          <Text style={tw`text-textSecondary mt-2`}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={tw`flex-1 bg-bgPrimary`}>
      <StatusBar backgroundColor="#79BF0D" barStyle="light-content" />
      
      {/* Header */}
      <View style={tw`bg-accentLight px-4 py-3 flex-row items-center`}>
        <TouchableOpacity onPress={handleBack} style={tw`mr-3`}>
          <Text style={tw`text-white text-xl`}></Text>
        </TouchableOpacity>
        <Text style={tw`text-white text-lg font-semibold`}>{getPageTitle()}</Text>
      </View>

      <ScrollView style={tw`flex-1 px-4 pt-6`}>
        
        {/* Entry Page Results */}
        {page === 'entry' && (
          <View style={tw`bg-green-100 rounded-2xl p-6 items-center mx-4`}>
            {entrySuccess ? (
              <>
                <Text style={tw`text-accentLight text-xl font-bold mb-6`}>
                  Entry Recorded
                </Text>
                <TouchableOpacity
                  style={tw`bg-accentLight px-8 py-3 rounded-lg`}
                  onPress={() => openQRScanner('entry', '')}
                >
                  <Text style={tw`text-white font-semibold`}>SCAN AGAIN</Text>
                </TouchableOpacity>
              </>
            ) : (
              <>
                <Text style={tw`text-red-600 text-lg font-bold mb-4 text-center`}>
                  {error || 'Entry Recording Failed'}
                </Text>
                <TouchableOpacity
                  style={tw`bg-accentLight px-8 py-3 rounded-lg`}
                  onPress={() => openQRScanner('entry', '')}
                >
                  <Text style={tw`text-white font-semibold`}>TRY AGAIN</Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        )}

        {/* Gifts Page Results */}
        {page === 'gifts' && (
          <View style={tw`mx-4`}>
            {error ? (
              <View style={tw`bg-red-100 rounded-2xl p-6 items-center`}>
                <Text style={tw`text-red-600 text-lg font-bold mb-4 text-center`}>
                  {error}
                </Text>
                <TouchableOpacity
                  style={tw`bg-accentLight px-8 py-3 rounded-lg`}
                  onPress={() => openQRScanner('gifts', '')}
                >
                  <Text style={tw`text-white font-semibold`}>TRY AGAIN</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <View style={tw`space-y-3`}>
                <Text style={tw`text-textPrimary text-lg font-bold mb-4 text-center`}>
                  Gift Status
                </Text>
                {Object.entries(GIFT_NAMES).map(([key, displayName]) => {
                  const received = gifts[key] === 1;
                  return (
                    <View
                      key={key}
                      style={tw`bg-white rounded-xl p-4 flex-row justify-between items-center border ${
                        received ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                      }`}
                    >
                      <Text style={tw`text-textPrimary font-medium`}>
                        {displayName}
                      </Text>
                      <View style={tw`flex-row items-center`}>
                        <View
                          style={tw`w-4 h-4 rounded-full mr-3 ${
                            received ? 'bg-green-500' : 'bg-red-500'
                          }`}
                        />
                        {!received && (
                          <TouchableOpacity
                            style={tw`bg-accentLight px-3 py-1 rounded-lg ${
                              updatingGift === key ? 'opacity-50' : ''
                            }`}
                            onPress={() => updateGiftStatus(key)}
                            disabled={updatingGift === key}
                          >
                            {updatingGift === key ? (
                              <ActivityIndicator size="small" color="white" />
                            ) : (
                              <Text style={tw`text-white text-xs font-semibold`}>
                                UPDATE
                              </Text>
                            )}
                          </TouchableOpacity>
                        )}
                      </View>
                    </View>
                  );
                })}
                
                <TouchableOpacity
                  style={tw`bg-accentLight px-8 py-3 rounded-lg mt-6 mx-8`}
                  onPress={() => openQRScanner('gifts', '')}
                >
                  <Text style={tw`text-white font-semibold text-center`}>SCAN AGAIN</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        )}

        {/* Generic Page Results */}
        {page !== 'entry' && page !== 'gifts' && (
          <View style={tw`mx-4`}>
            {error ? (
              <View style={tw`bg-red-100 rounded-2xl p-6 items-center`}>
                <Text style={tw`text-red-600 text-lg font-bold mb-4 text-center`}>
                  Not Allowed
                </Text>
                <Text style={tw`text-red-600 text-center mb-4`}>
                  {error}
                </Text>
                <TouchableOpacity
                  style={tw`bg-accentLight px-8 py-3 rounded-lg`}
                  onPress={() => openQRScanner(page, segment)}
                >
                  <Text style={tw`text-white font-semibold`}>TRY AGAIN</Text>
                </TouchableOpacity>
              </View>
            ) : genericData ? (
              <View style={tw`bg-white rounded-2xl p-6`}>
                {genericData.allowed === false ? (
                  <>
                    <Text style={tw`text-red-600 text-lg font-bold mb-4 text-center`}>
                      Not Allowed
                    </Text>
                    <TouchableOpacity
                      style={tw`bg-accentLight px-8 py-3 rounded-lg`}
                      onPress={() => openQRScanner(page, segment)}
                    >
                      <Text style={tw`text-white font-semibold text-center`}>SCAN AGAIN</Text>
                    </TouchableOpacity>
                  </>
                ) : (
                  <>
                    <Text style={tw`text-accentLight text-xl font-bold mb-4 text-center`}>
                      Access Granted
                    </Text>
                    {genericData.name && (
                      <Text style={tw`text-textPrimary text-lg mb-2 text-center`}>
                        Welcome, {genericData.name}
                      </Text>
                    )}
                    {/* Display other data */}
                    {Object.entries(genericData).map(([key, value]) => {
                      if (key !== 'allowed' && key !== 'name' && key !== 'error') {
                        return (
                          <View key={key} style={tw`flex-row justify-between mb-2`}>
                            <Text style={tw`text-textSecondary capitalize`}>
                              {key.replace(/_/g, ' ')}:
                            </Text>
                            <Text style={tw`text-textPrimary`}>
                              {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                            </Text>
                          </View>
                        );
                      }
                    })}
                    <TouchableOpacity
                      style={tw`bg-accentLight px-8 py-3 rounded-lg mt-4`}
                      onPress={() => openQRScanner(page, segment)}
                    >
                      <Text style={tw`text-white font-semibold text-center`}>SCAN AGAIN</Text>
                    </TouchableOpacity>
                  </>
                )}
              </View>
            ) : null}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};