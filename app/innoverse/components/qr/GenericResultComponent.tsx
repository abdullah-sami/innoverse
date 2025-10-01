import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { create } from 'twrnc';
import { INNOVERSE_API_CONFIG } from '@/services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const tw = create(require('../../tailwind.twrnc.config.js'));

interface GenericResultProps {
  page: string;
  segment: string;
  qr_code_data: string;
}

interface GenericResponse {
  allowed: boolean;
  name?: string;
  error?: string;
  [key: string]: any;
}

export const GenericResultComponent: React.FC<GenericResultProps> = ({ page, segment, qr_code_data }) => {
  const navigation = useNavigation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [genericData, setGenericData] = useState<GenericResponse | null>(null);

  const getHeaders = async () => {
    const token = await AsyncStorage.getItem("access_token");
    return {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  };

  const fetchGenericData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const headers = await getHeaders();
      const endpoint = segment 
        ? `${INNOVERSE_API_CONFIG.BASE_URL}/api/check/${page}/${segment}/${qr_code_data}/`
        : `${INNOVERSE_API_CONFIG.BASE_URL}/api/${page}/${qr_code_data}/`;
      
      console.log('Generic - Headers:', headers);
      console.log('Generic - URL:', endpoint);
      
      const response = await fetch(endpoint, {
        method: 'GET',
        headers,
      });

      console.log('Generic - Response status:', response.status);

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
        setError(errorData.error || `Request failed (${response.status})`);
      }
    } catch (err) {
      console.error('Generic fetch error:', err);
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

  const openQRScanner = () => {
    navigation.navigate('qr_scanner' as never, { page: page, segment: segment } as never);
  };

  const goToHome = () => {
    navigation.navigate('(tabs)' as never);
  };

  useEffect(() => {
    fetchGenericData();
  }, [page, segment, qr_code_data]);

  if (loading) {
    return (
      <View style={tw`flex-1 justify-center items-center`}>
        <ActivityIndicator size="large" color="#79BF0D" />
        <Text style={tw`text-textSecondary mt-2`}>Processing...</Text>
      </View>
    );
  }

  return (
    <View style={tw`mx-4`}>
      {error ? (
        <View style={tw`bg-red-100 rounded-2xl p-6 items-center border border-red-200`}>
          <View style={tw`w-16 h-16 bg-red-500 rounded-full items-center justify-center mb-4`}>
            <Text style={tw`text-white text-2xl font-bold`}>✕</Text>
          </View>
          <Text style={tw`text-red-800 text-lg font-bold mb-2 text-center`}>
            Access Denied
          </Text>
          <Text style={tw`text-red-700 text-center mb-6`}>
            {error}
          </Text>
          <View style={tw`flex-row space-x-3`}>
            <TouchableOpacity
              style={tw`bg-red-600 px-8 py-3 rounded-lg shadow-sm`}
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
      ) : genericData ? (
        <View style={tw`bg-white rounded-2xl p-6 border shadow-sm`}>
          {genericData.allowed === false ? (
            <>
              <View style={tw`w-16 h-16 bg-red-500 rounded-full items-center justify-center mb-4 self-center`}>
                <Text style={tw`text-white text-2xl font-bold`}>✕</Text>
              </View>
              <Text style={tw`text-red-800 text-lg font-bold mb-4 text-center`}>
                Access Denied
              </Text>
              <View style={tw`flex-row space-x-3`}>
                <TouchableOpacity
                  style={tw`flex-1 bg-red-600 px-8 py-3 rounded-lg shadow-sm px-3 mx-1`}
                  onPress={openQRScanner}
                >
                  <Text style={tw`text-white font-semibold text-center`}>SCAN AGAIN</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={tw`flex-1 bg-gray-600 px-8 py-3 rounded-lg shadow-sm px-3 mx-1`}
                  onPress={goToHome}
                >
                  <Text style={tw`text-white font-semibold text-center`}>HOME</Text>
                </TouchableOpacity>
              </View>
            </>
          ) : (
            <>
              <View style={tw`w-16 h-16 bg-green-500 rounded-full items-center justify-center mb-4 self-center`}>
                <Text style={tw`text-white text-2xl font-bold`}>✓</Text>
              </View>
              <Text style={tw`text-green-800 text-xl font-bold mb-4 text-center`}>
                Access Granted
              </Text>
              {genericData.name && (
                <Text style={tw`text-textPrimary text-lg mb-4 text-center`}>
                  Welcome, {genericData.name}!
                </Text>
              )}
              
              {Object.entries(genericData).map(([key, value]) => {
                if (key !== 'allowed' && key !== 'name' && key !== 'error') {
                  return (
                    <View key={key} style={tw`flex-row justify-between py-2 border-b border-gray-100`}>
                      <Text style={tw`text-textSecondary capitalize font-medium`}>
                        {key.replace(/_/g, ' ')}:
                      </Text>
                      <Text style={tw`text-textPrimary`}>
                        {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                      </Text>
                    </View>
                  );
                }
              })}
              <View style={tw`flex-row space-x-3 mt-6`}>
                <TouchableOpacity
                  style={tw`flex-1 bg-accentLight px-8 py-3 rounded-lg shadow-sm px-3 mx-1`}
                  onPress={openQRScanner}
                >
                  <Text style={tw`text-white font-semibold text-center`}>SCAN ANOTHER</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={tw`flex-1 bg-gray-600 px-8 py-3 rounded-lg shadow-sm px-3 mx-1`}
                  onPress={goToHome}
                >
                  <Text style={tw`text-white font-semibold text-center`}>HOME</Text>
                </TouchableOpacity>
              </View>
            </>
          )}
        </View>
      ) : null}
    </View>
  );
};