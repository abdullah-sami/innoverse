import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { create } from 'twrnc';
import { INNOVERSE_API_CONFIG } from '@/services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const tw = create(require('../../tailwind.twrnc.config.js'));

interface EntryResultProps {
  qr_code_data: string;
}

interface EntryResponse {
  success: boolean;
  data?: {
    p_name?: string | null;
    t_name?: string | null;
  };
  error?: string;
  errors?: { [key: string]: string[] };
}

export const EntryResultComponent: React.FC<EntryResultProps> = ({ qr_code_data }) => {
  const navigation = useNavigation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [entrySuccess, setEntrySuccess] = useState(false);

  const [participantInfo, setParticipantInfo] = useState<string | null>(null);
  const [teamInfo, setTeamInfo] = useState<string | null>(null);

  const getHeaders = async () => {
    const token = await AsyncStorage.getItem("access_token");
    return {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  };

  const formatErrorMessage = (data: EntryResponse): string => {
    if (data.error) {
      return data.error;
    }

    if (data.errors) {
      const errorMessages: string[] = [];
      Object.entries(data.errors).forEach(([field, messages]) => {
        if (Array.isArray(messages)) {
          errorMessages.push(...messages);
        } else {
          errorMessages.push(String(messages));
        }
      });
      return errorMessages.join('. ');
    }

    return 'An unknown error occurred';
  };

  const recordEntry = async () => {
    setLoading(true);
    setError(null);
    setParticipantInfo(null);
    setTeamInfo(null);

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

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const textResponse = await response.text();
        console.log('Entry recording - Non-JSON response:', textResponse);
        throw new Error('Server returned non-JSON response');
      }

      const data: EntryResponse = await response.json();
      console.log('Entry recording - Response data:', data);

      if (response.status === 201 && data.success) {
        setEntrySuccess(true);
        setError(null);
        
        if (data.data) {
          if (data.data.p_name) {
            setParticipantInfo(data.data.p_name);
          }
          if (data.data.t_name) {
            setTeamInfo(data.data.t_name);
          }
        }
      }
      else {
        setEntrySuccess(false);

        let errorMessage: string;

        if (response.status === 404) {
          errorMessage = data.error || 'QR code not found or invalid';
        } else if (response.status === 400) {
          errorMessage = data.error || formatErrorMessage(data);
        } else if (response.status === 401) {
          errorMessage = 'Authentication required. Please log in again.';
        } else if (response.status === 403) {
          errorMessage = 'You do not have permission to perform this action.';
        } else {
          errorMessage = data.error || formatErrorMessage(data) || `Server error (${response.status})`;
        }

        setError(errorMessage);
      }
    } catch (err) {
      console.error('Entry recording error:', err);
      setEntrySuccess(false);

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
    navigation.navigate('qr_scanner', { page: 'entry', segment: '' });
  };

  const goToHome = () => {
    navigation.navigate('(tabs)' as never);
  };

  useEffect(() => {
    recordEntry();
  }, [qr_code_data]);

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
      {entrySuccess ? (
        <>
          <View style={tw`bg-green-100 rounded-2xl p-6 items-center border border-green-200`}>
            <View style={tw`w-16 h-16 bg-green-500 rounded-full items-center justify-center mb-4`}>
              <Text style={tw`text-white text-2xl font-bold`}>✓</Text>
            </View>
            <Text style={tw`text-green-800 text-xl font-bold mb-2`}>
              Entry Recorded Successfully!
            </Text>
            <Text style={tw`text-green-700 text-center mb-6`}>
              The entry has been recorded in the system.
            </Text>
            <View style={tw`flex-row space-x-3`}>
              <TouchableOpacity
                style={tw`bg-accentLight px-8 py-3 rounded-lg shadow-sm mr-2`}
                onPress={openQRScanner}
              >
                <Text style={tw`text-white font-semibold`}>SCAN ANOTHER</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={tw`bg-gray-600 px-8 py-3 rounded-lg shadow-sm`}
                onPress={goToHome}
              >
                <Text style={tw`text-white font-semibold`}>HOME</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Participant/Team Info Section */}
          {(participantInfo || teamInfo) && (
            <View style={tw`bg-white rounded-2xl p-6 items-center border border-green-200 mt-5 shadow-sm`}>
              <Text style={tw`text-green-800 text-center mb-4 text-lg font-semibold`}>
                Participant/Team Information
              </Text>
              
              {participantInfo && (
                <View style={tw`mb-3 w-full`}>
                  <Text style={tw`text-gray-600 text-sm font-medium mb-1`}>Participant Name:</Text>
                  <Text style={tw`text-gray-800 text-base font-semibold`}>{participantInfo}</Text>
                </View>
              )}
              
              {teamInfo && (
                <View style={tw`w-full`}>
                  <Text style={tw`text-gray-600 text-sm font-medium mb-1`}>Team Name:</Text>
                  <Text style={tw`text-gray-800 text-base font-semibold`}>{teamInfo}</Text>
                </View>
              )}
            </View>
          )}
        </>
      ) : (
        <View style={tw`bg-red-100 rounded-2xl p-6 items-center border border-red-200`}>
          <View style={tw`w-16 h-16 bg-red-500 rounded-full items-center justify-center mb-4`}>
            <Text style={tw`text-white text-2xl font-bold`}>✕</Text>
          </View>
          <Text style={tw`text-red-800 text-xl font-bold mb-2 text-center`}>
            Entry Recording Failed
          </Text>
          <Text style={tw`text-red-700 text-center mb-6 leading-5`}>
            {error || 'Unable to record entry. Please try again.'}
          </Text>
          <View style={tw`flex-row space-x-3`}>
            <TouchableOpacity
              style={tw`bg-red-600 px-8 py-3 rounded-lg shadow-sm  mr-2`}
              onPress={openQRScanner}
            >
              <Text style={tw`text-white font-semibold`}>SCAN AGAIN</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={tw`bg-gray-600 px-8 py-3 rounded-lg shadow-sm`}
              onPress={goToHome}
            >
              <Text style={tw`text-white font-semibold`}>HOME</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
};