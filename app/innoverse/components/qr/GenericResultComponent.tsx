import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, ScrollView } from 'react-native';
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

interface GenericResponse {
  allowed: boolean;
  page?: string;
  event?: string;
  segment?: string;
  participant?: ParticipantInfo;
  team?: TeamInfo;
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
      
      // console.log('Generic - URL:', endpoint);
      
      const response = await fetch(endpoint, {
        method: 'GET',
        headers,
      });

      // console.log('Generic - Response status:', response.status);

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
      <View style={tw`flex-row justify-between py-2.5 border-b border-gray-100`}>
        <Text style={tw`text-gray-600 font-medium flex-1`}>{label}:</Text>
        <Text style={tw`text-gray-900 font-semibold text-right`}>
          {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
        </Text>
      </View>
    );
  };

  const ParticipantCard = ({ participant }: { participant: ParticipantInfo }) => (
    <View style={tw`bg-white rounded-xl p-5 border border-gray-200 shadow-sm mb-4`}>
      <View style={tw`flex-row justify-between items-start mb-4`}>
        <View style={tw`flex-1`}>
          <Text style={tw`text-xl font-bold text-gray-800 mb-1`}>{participant.name}</Text>
          <Text style={tw`text-gray-600 text-sm`}>ID: {participant.id}</Text>
        </View>
        <StatusBadge verified={participant.payment_verified} />
      </View>
      
      <View style={tw`mt-2`}>
        <InfoRow label="Email" value={participant.email} />
        <InfoRow label="Phone" value={participant.phone} />
        {participant.guardian_phone && <InfoRow label="Guardian Phone" value={participant.guardian_phone} />}
        {participant.grade && <InfoRow label="Grade" value={participant.grade} />}
        <InfoRow label="Institution" value={participant.institution} />
      </View>
    </View>
  );

  const TeamCard = ({ team }: { team: TeamInfo }) => (
    <View style={tw`bg-white rounded-xl p-5 border border-gray-200 shadow-sm mb-4`}>
      <View style={tw`flex-row justify-between items-start mb-4`}>
        <View style={tw`flex-1`}>
          <Text style={tw`text-xl font-bold text-gray-800 mb-1`}>{team.name}</Text>
          <Text style={tw`text-gray-600 text-sm`}>Team ID: {team.id} • {team.member_count} Members</Text>
        </View>
        <StatusBadge verified={team.payment_verified} />
      </View>

      <View style={tw`mt-4`}>
        <Text style={tw`text-gray-700 font-bold text-base mb-3`}>Team Members</Text>
        {team.members.map((member, index) => (
          <View key={index} style={tw`bg-gray-50 rounded-lg p-3 mb-2 border border-gray-200`}>
            <View style={tw`flex-row justify-between items-center mb-2`}>
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
  );

  if (loading) {
    return (
      <View style={tw`flex-1 justify-center items-center py-20`}>
        <ActivityIndicator size="large" color="#79BF0D" />
        <Text style={tw`text-gray-600 mt-2`}>Processing...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={tw`flex-1`} contentContainerStyle={tw`mx-4 pb-6`}>
      {error ? (
        <View style={tw`bg-red-100 rounded-2xl p-6 items-center border border-red-200`}>
          <View style={tw`w-16 h-16 bg-red-500 rounded-full items-center justify-center mb-4`}>
            <Text style={tw`text-white text-2xl font-bold`}>✕</Text>
          </View>
          <Text style={tw`text-red-800 text-xl font-bold mb-2 text-center`}>
            Error
          </Text>
          <Text style={tw`text-red-700 text-center mb-6 leading-5`}>
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
      ) : genericData ? (
        <>
          {/* Status Card */}
          <View style={tw`${genericData.allowed ? 'bg-green-100 border-green-200' : 'bg-red-100 border-red-200'} rounded-2xl p-6 items-center border mb-4`}>
            <View style={tw`w-16 h-16 ${genericData.allowed ? 'bg-green-500' : 'bg-red-500'} rounded-full items-center justify-center mb-4`}>
              <Text style={tw`text-white text-2xl font-bold`}>
                {genericData.allowed ? '✓' : '✕'}
              </Text>
            </View>
            <Text style={tw`${genericData.allowed ? 'text-green-800' : 'text-red-800'} text-2xl font-bold mb-2`}>
              {genericData.allowed ? 'Access Granted' : 'Access Denied'}
            </Text>
            
            {/* Event/Segment Info */}
            {(genericData.event || genericData.segment) && (
              <View style={tw`mt-3`}>
                {genericData.event && (
                  <Text style={tw`${genericData.allowed ? 'text-green-700' : 'text-red-700'} text-base font-medium text-center capitalize`}>
                    Event: {genericData.event}
                  </Text>
                )}
                {genericData.segment && (
                  <Text style={tw`${genericData.allowed ? 'text-green-700' : 'text-red-700'} text-base font-medium text-center capitalize`}>
                    Segment: {genericData.segment}
                  </Text>
                )}
              </View>
            )}
          </View>

          {/* Only show participant/team info if access is granted */}
          {genericData.allowed && (
            <>
              {/* Participant Information */}
              {genericData.participant && (
                <>
                  <Text style={tw`text-gray-800 text-lg font-bold mb-3`}>Participant Information</Text>
                  <ParticipantCard participant={genericData.participant} />
                </>
              )}

              {/* Team Information */}
              {genericData.team && (
                <>
                  <Text style={tw`text-gray-800 text-lg font-bold mb-3`}>Team Information</Text>
                  <TeamCard team={genericData.team} />
                </>
              )}

              {/* Additional metadata */}
              {Object.entries(genericData).some(([key]) => 
                !['allowed', 'page', 'event', 'segment', 'participant', 'team', 'error'].includes(key)
              ) && (
                <View style={tw`bg-white rounded-xl p-5 border border-gray-200 shadow-sm mb-4`}>
                  <Text style={tw`text-gray-800 text-lg font-bold mb-3`}>Additional Information</Text>
                  {Object.entries(genericData).map(([key, value]) => {
                    if (!['allowed', 'page', 'event', 'segment', 'participant', 'team', 'error'].includes(key)) {
                      return (
                        <InfoRow 
                          key={key} 
                          label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} 
                          value={value}
                        />
                      );
                    }
                  })}
                </View>
              )}
            </>
          )}

          {/* Action Buttons */}
          <View style={tw`flex-row justify-center mt-2`}>
            <TouchableOpacity
              style={tw`${genericData.allowed ? 'bg-accentLight' : 'bg-red-600'} px-8 py-3 rounded-lg shadow-sm mr-2`}
              onPress={openQRScanner}
            >
              <Text style={tw`text-white font-semibold`}>
                {genericData.allowed ? 'SCAN ANOTHER' : 'TRY AGAIN'}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={tw`bg-gray-600 px-8 py-3 rounded-lg shadow-sm`}
              onPress={goToHome}
            >
              <Text style={tw`text-white font-semibold`}>HOME</Text>
            </TouchableOpacity>
          </View>
        </>
      ) : null}
    </ScrollView>
  );
};