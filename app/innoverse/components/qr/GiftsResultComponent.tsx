import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, Animated, ScrollView } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { create } from 'twrnc';
import { INNOVERSE_API_CONFIG } from '@/services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const tw = create(require('../../tailwind.twrnc.config.js'));

interface GiftsResultProps {
  qr_code_data: string;
}

interface GiftStatus {
  tshirt: number;
  breakfast: number;
  notebook: number;
  snacks: number;
}

interface ParticipantInfo {
  id: number;
  name: string;
  email: string;
  phone: string;
  institution: string;
  guardian_phone?: string | null;
  grade?: string;
  payment_verified: boolean;
}

interface TeamMember {
  name: string;
  email: string;
  is_leader: boolean;
}

interface TeamInfo {
  id: number;
  name: string;
  member_count: number;
  payment_verified: boolean;
  members: TeamMember[];
}

interface GiftsResponse {
  gifts: GiftStatus;
  participant?: ParticipantInfo;
  team?: TeamInfo;
}

const GIFT_NAMES: Record<keyof GiftStatus, string> = {
  tshirt: 'T-Shirt',
  breakfast: 'Breakfast',
  notebook: 'Notebook',
  snacks: 'Snacks'
};

const Toast = ({ message, visible, type }: { message: string; visible: boolean; type: 'success' | 'error' }) => {
  const slideAnim = useRef(new Animated.Value(100)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
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
  const [data, setData] = useState<GiftsResponse | null>(null);
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
      
      const response = await fetch(
        `${INNOVERSE_API_CONFIG.BASE_URL}/api/gifts/${qr_code_data}/`,
        {
          method: 'GET',
          headers,
        }
      );

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const textResponse = await response.text();
        throw new Error('Server returned non-JSON response');
      }

      if (response.ok) {
        const responseData: GiftsResponse = await response.json();
        setData(responseData);
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

      if (response.ok) {
        const responseData = await response.json();
        
        if (responseData.message) {
          showToast(responseData.message, 'success');
        } else {
          showToast(`${GIFT_NAMES[giftName as keyof GiftStatus]} marked as received!`, 'success');
        }
        
        await getGifts();
      } else {
        let errorMessage = `Failed to update ${GIFT_NAMES[giftName as keyof GiftStatus]} status`;
        
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch (parseError) {
          errorMessage = response.statusText || errorMessage;
        }
        
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

  const StatusBadge = ({ verified }: { verified: boolean }) => (
    <View style={tw`${verified ? 'bg-green-500' : 'bg-red-500'} px-3 py-1 rounded-full`}>
      <Text style={tw`text-white font-bold text-xs`}>
        {verified ? '✓ VERIFIED' : '✗ NOT VERIFIED'}
      </Text>
    </View>
  );

  const InfoRow = ({ label, value }: { label: string; value: string | number | boolean | null | undefined }) => {
    if (value === null || value === undefined || value === '') return null;
    
    return (
      <View style={tw`flex-row justify-between py-2 border-b border-gray-100`}>
        <Text style={tw`text-gray-600 font-medium flex-1`}>{label}:</Text>
        <Text style={tw`text-gray-900 font-semibold flex-1 text-right`}>
          {String(value)}
        </Text>
      </View>
    );
  };

  if (loading && !data) {
    return (
      <View style={tw`flex-1 justify-center items-center py-20`}>
        <ActivityIndicator size="large" color="#79BF0D" />
        <Text style={tw`text-gray-600 mt-2`}>Loading gifts...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={tw`flex-1`} contentContainerStyle={tw`pb-6`}>
      <View style={tw`mx-4 relative`}>
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
        ) : data ? (
          <>
          {/* Gift Status */}
            <View style={tw`bg-white rounded-xl p-5 mb-4 border border-gray-200 shadow-sm`}>
              <Text style={tw`text-gray-800 text-xl font-bold mb-4`}>Gift Status</Text>
              
              {Object.entries(GIFT_NAMES).map(([key, displayName]) => {
                const received = data.gifts[key as keyof GiftStatus] === 1;
                const isUpdating = updatingGift === key;
                
                return (
                  <View
                    key={key}
                    style={tw`flex-row justify-between items-center p-4 mb-3 rounded-lg border ${
                      received ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <View style={tw`flex-row items-center flex-1`}>
                      <View
                        style={tw`w-3 h-3 rounded-full mr-3 ${
                          received ? 'bg-green-500' : 'bg-gray-400'
                        }`}
                      />
                      <Text style={tw`text-gray-800 font-semibold text-base`}>
                        {displayName}
                      </Text>
                    </View>
                    
                    <View style={tw`flex-row items-center`}>
                      {received ? (
                        <View style={tw`bg-green-500 px-3 py-1.5 rounded-full`}>
                          <Text style={tw`text-white text-xs font-bold`}>
                            ✓ RECEIVED
                          </Text>
                        </View>
                      ) : (
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
                              MARK RECEIVED
                            </Text>
                          )}
                        </TouchableOpacity>
                      )}
                    </View>
                  </View>
                );
              })}
            </View>
            
            {/* Participant Info */}
            {data.participant && (
              <View style={tw`bg-white rounded-xl p-5 mb-4 border border-gray-200 shadow-sm`}>
                <View style={tw`flex-row justify-between items-start mb-3`}>
                  <View style={tw`flex-1`}>
                    <Text style={tw`text-xl font-bold text-gray-800 mb-1`}>
                      {data.participant.name}
                    </Text>
                    <Text style={tw`text-gray-600 text-sm`}>ID: {data.participant.id}</Text>
                  </View>
                  <StatusBadge verified={data.participant.payment_verified} />
                </View>
                
                <View style={tw`mt-2`}>
                  <InfoRow label="Email" value={data.participant.email} />
                  <InfoRow label="Phone" value={data.participant.phone} />
                  {data.participant.guardian_phone && (
                    <InfoRow label="Guardian Phone" value={data.participant.guardian_phone} />
                  )}
                  {data.participant.grade && <InfoRow label="Grade" value={data.participant.grade} />}
                  <InfoRow label="Institution" value={data.participant.institution} />
                </View>
              </View>
            )}

            {/* Team Info */}
            {data.team && (
              <View style={tw`bg-white rounded-xl p-5 mb-4 border border-gray-200 shadow-sm`}>
                <View style={tw`flex-row justify-between items-start mb-3`}>
                  <View style={tw`flex-1`}>
                    <Text style={tw`text-xl font-bold text-gray-800 mb-1`}>
                      {data.team.name}
                    </Text>
                    <Text style={tw`text-gray-600 text-sm`}>
                      Team ID: {data.team.id} • {data.team.member_count} Members
                    </Text>
                  </View>
                  <StatusBadge verified={data.team.payment_verified} />
                </View>

                <View style={tw`mt-3`}>
                  <Text style={tw`text-gray-700 font-bold text-base mb-2`}>Team Members</Text>
                  {data.team.members.map((member, index) => (
                    <View key={index} style={tw`bg-gray-50 rounded-lg p-3 mb-2 border border-gray-200`}>
                      <View style={tw`flex-row justify-between items-center mb-1`}>
                        <Text style={tw`text-gray-900 font-semibold flex-1`}>{member.name}</Text>
                        {member.is_leader && (
                          <View style={tw`bg-blue-500 px-2 py-1 rounded-full`}>
                            <Text style={tw`text-white text-xs font-bold`}>LEADER</Text>
                          </View>
                        )}
                      </View>
                      <Text style={tw`text-gray-600 text-sm`}>{member.email}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            

            {/* Action Buttons */}
            <View style={tw`flex-row justify-center mt-2 mb-10`}>
              <TouchableOpacity
                style={tw`bg-accentLight px-8 py-3 rounded-lg shadow-sm mr-2 ${
                  loading ? 'opacity-50' : ''
                }`}
                onPress={openQRScanner}
                disabled={loading}
              >
                <Text style={tw`text-white font-semibold`}>SCAN ANOTHER</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={tw`bg-gray-600 px-8 py-3 rounded-lg shadow-sm ${
                  loading ? 'opacity-50' : ''
                }`}
                onPress={goToHome}
                disabled={loading}
              >
                <Text style={tw`text-white font-semibold`}>HOME</Text>
              </TouchableOpacity>
            </View>
          </>
        ) : null}
        
        <Toast message={toast.message} visible={toast.visible} type={toast.type} />
      </View>
    </ScrollView>
  );
};