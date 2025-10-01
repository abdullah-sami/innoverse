import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, Animated, Dimensions } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { create } from 'twrnc';
import { INNOVERSE_API_CONFIG } from '@/services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const tw = create(require('../../tailwind.twrnc.config.js'));

interface GiftsResultProps {
  qr_code_data: string;
}

interface GiftsResponse {
  tshirt?: number;
  breakfast?: number;
  notebook?: number;
  snacks?: number;
  [key: string]: number | undefined;
}

const GIFT_NAMES = {
  tshirt: 'T-Shirt',
  breakfast: 'Breakfast',
  notebook: 'Notebook',
  snacks: 'Snacks'
};

const { width } = Dimensions.get('window');

const Toast = ({ message, visible, type }: { message: string; visible: boolean; type: 'success' | 'error' }) => {
  const slideAnim = useRef(new Animated.Value(100)).current; // Start below screen
  const opacityAnim = useRef(new Animated.Value(0)).current; // Start invisible

  useEffect(() => {
    if (visible) {
      // Slide up and fade in
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(opacityAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      // Slide down and fade out
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: 100,
          duration: 250,
          useNativeDriver: true,
        }),
        Animated.timing(opacityAnim, {
          toValue: 0,
          duration: 250,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible, slideAnim, opacityAnim]);

  if (!visible && slideAnim._value === 100) return null;

  return (
    <View style={tw`absolute bottom-0 left-0 right-0 z-50 px-4 pb-6`}>
      <Animated.View
        style={[
          tw`${type === 'success' ? 'bg-green-500' : 'bg-red-500'} px-4 py-3 rounded-lg shadow-lg mx-2`,
          {
            transform: [{ translateY: slideAnim }],
            opacity: opacityAnim,
          },
        ]}
      >
        <View style={tw`flex-row items-center justify-center`}>
          <Text style={tw`text-white text-lg mr-2`}>
            {type === 'success' ? '✓' : '✕'}
          </Text>
          <Text style={tw`text-white font-medium text-center flex-1`}>
            {message}
          </Text>
        </View>
      </Animated.View>
    </View>
  );
};

export const GiftsResultComponent: React.FC<GiftsResultProps> = ({ qr_code_data }) => {
  const navigation = useNavigation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [gifts, setGifts] = useState<GiftsResponse>({});
  const [updatingGift, setUpdatingGift] = useState<string | null>(null);
  const [toast, setToast] = useState({ visible: false, message: '', type: 'success' as 'success' | 'error' });

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ visible: true, message, type });
    setTimeout(() => {
      setToast(prev => ({ ...prev, visible: false }));
    }, 3000);
  };

  const getHeaders = async () => {
    const token = await AsyncStorage.getItem("access_token");
    return {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  };

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
        setError(errorData.error || `Failed to fetch gifts (${response.status})`);
      }
    } catch (err: any) {
      console.error('Gifts fetching error:', err);
      if (err.message.includes('JSON Parse error') || err.message.includes('non-JSON response')) {
        setError('Server error. Please check your connection and try again.');
      } else if (err.message.includes('Network request failed') || err.message.includes('fetch')) {
        setError('Network error. Please check your internet connection.');
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const updateGiftStatus = async (giftName: string) => {
    setUpdatingGift(giftName);
    
    try {
      const headers = await getHeaders();
      console.log('Updating gift status for:', giftName);
      console.log('Update URL:', `${INNOVERSE_API_CONFIG.BASE_URL}/api/gifts/${qr_code_data}/`);
      
      const response = await fetch(
        `${INNOVERSE_API_CONFIG.BASE_URL}/api/gifts/${qr_code_data}/`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({ 
            gift_name: giftName 
          }),
        }
      );

      console.log('Gift update response status:', response.status);

      if (response.ok) {
        const responseData = await response.json();
        console.log('Gift update success:', responseData);
        
        if (responseData.message) {
          showToast(responseData.message, 'success');
        } else {
          showToast(`${GIFT_NAMES[giftName]} marked as received!`, 'success');
        }
        
        await getGifts();
      } else {
        let errorMessage = `Failed to update ${GIFT_NAMES[giftName]} status`;
        
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch (parseError) {
          errorMessage = response.statusText || errorMessage;
        }
        
        console.error('Gift update error:', errorMessage);
        showToast(errorMessage, 'error');
      }
    } catch (err: any) {
      console.error('Gift update network error:', err);
      let errorMessage = 'Network error. Please try again.';
      
      if (err.message.includes('Network request failed')) {
        errorMessage = 'Network error. Please check your internet connection.';
      } else if (err.message.includes('JSON')) {
        errorMessage = 'Server error. Please try again.';
      }
      
      showToast(errorMessage, 'error');
    } finally {
      setUpdatingGift(null);
    }
  };

  const openQRScanner = () => {
    navigation.navigate('qr_scanner' as never, { page: 'gifts', segment: '' } as never);
  };

  const goToHome = () => {
    navigation.navigate('(tabs)' as never);
  };

  useEffect(() => {
    if (qr_code_data) {
      getGifts();
    }
  }, [qr_code_data]);

  return (
    <View style={tw`mx-4 relative flex-1`}>
      {error ? (
        <View style={tw`bg-red-100 rounded-2xl p-6 items-center border border-red-200`}>
          <View style={tw`w-16 h-16 bg-red-500 rounded-full items-center justify-center mb-4`}>
            <Text style={tw`text-white text-2xl font-bold`}>✕</Text>
          </View>
          <Text style={tw`text-red-800 text-lg font-bold mb-2 text-center`}>
            Unable to Load Gifts
          </Text>
          <Text style={tw`text-red-700 text-center mb-6`}>
            {error}
          </Text>
          <View style={tw`flex-row space-x-3`}>
            <TouchableOpacity
              style={tw`bg-red-600 px-8 py-3 rounded-lg shadow-sm mr-2`}
              onPress={openQRScanner}
            >
              <Text style={tw`text-white font-semibold`}>TRY AGAIN</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={tw`bg-gray-600 px-8 py-3 rounded-lg shadow-sm`}
              onPress={goToHome}
            >
              <Text style={tw`text-white font-semibold`}>HOME</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <View style={tw`space-y-4`}>
          {loading && (
            <View style={tw`items-center py-4`}>
              <ActivityIndicator size="large" color="#79BF0D" />
              <Text style={tw`text-textSecondary mt-2`}>Loading gifts...</Text>
            </View>
          )}
          
          <Text style={tw`text-textPrimary text-lg font-bold mb-4 text-center`}>
            Gift Status
          </Text>
          
          {Object.entries(GIFT_NAMES).map(([key, displayName]) => {
            const received = gifts[key] === 1;
            const isUpdating = updatingGift === key;
            
            return (
              <View
                key={key}
                style={tw`bg-white rounded-xl p-4 flex-row justify-between items-center border shadow-sm mb-3 ${
                  received ? 'border-green-200 bg-green-50' : 'border-gray-200'
                }`}
              >
                <View style={tw`flex-row items-center flex-1`}>
                  <View
                    style={tw`w-4 h-4 rounded-full mr-3 ${
                      received ? 'bg-green-500' : 'bg-gray-400'
                    }`}
                  />
                  <Text style={tw`text-textPrimary font-medium`}>
                    {displayName}
                  </Text>
                </View>
                
                <View style={tw`flex-row items-center`}>
                  <Text style={tw`text-sm mr-3 ${
                    received ? 'text-green-700' : 'text-gray-600'
                  }`}>
                    {received ? 'Received' : 'Not Received'}
                  </Text>
                  {!received && (
                    <TouchableOpacity
                      style={tw`bg-accentLight px-4 py-2 rounded-full shadow-md ${
                        isUpdating || loading ? 'opacity-50' : ''
                      }`}
                      onPress={() => updateGiftStatus(key)}
                      disabled={isUpdating || loading}
                    >
                      {isUpdating ? (
                        <View style={tw`flex-row items-center`}>
                          <ActivityIndicator size="small" color="white" />
                          <Text style={tw`text-white text-xs font-semibold ml-2`}>
                            UPDATING...
                          </Text>
                        </View>
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
          
          <View style={tw`flex-row space-x-3 mt-6 mx-4 mb-20`}>
            <TouchableOpacity
              style={tw`flex-1 bg-accentLight px-8 py-3 rounded-lg shadow-sm mr-3 px-3 mx-1 ${
                loading ? 'opacity-50' : ''
              }`}
              onPress={openQRScanner}
              disabled={loading}
            >
              <Text style={tw`text-white font-semibold text-center`}>SCAN ANOTHER</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={tw`flex-1 bg-gray-600 px-8 py-3 rounded-lg shadow-sm px-3 mx-1 ${
                loading ? 'opacity-50' : ''
              }`}
              onPress={goToHome}
              disabled={loading}
            >
              <Text style={tw`text-white font-semibold text-center`}>HOME</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
      
      <Toast message={toast.message} visible={toast.visible} type={toast.type} />
    </View>
  );
};