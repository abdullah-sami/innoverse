import React, { useEffect, useState } from 'react';
import { View, Text, ActivityIndicator, ScrollView, TouchableOpacity } from 'react-native';
import { create } from 'twrnc';
import { useNavigation } from '@react-navigation/native';
import { INNOVERSE_API_CONFIG } from '@/services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const tw = create(require('../../tailwind.twrnc.config.js'));

interface Participant {
  id: number;
  f_name: string;
  l_name: string;
  email: string;
  phone: string;
  age: number;
  institution: string;
  institution_id: string;
  address: string;
  payment_verified: boolean;
  segment_list: string[];
  comp_list: string[];
  gift_list: string[];
  entry_status: boolean;
}

interface TeamMember {
  id: number;
  f_name: string;
  l_name: string;
  email: string;
  phone: string;
  age: number;
  institution: string;
  institution_id: string;
  is_leader: boolean;
}

interface Team {
  id: number;
  team_name: string;
  payment_verified: boolean;
  comp_list: string[];
  gift_list: string[];
  entry_status: boolean;
  members: TeamMember[];
}

interface ApiResponse {
  participant?: Participant;
  team?: Team;
}

interface InfoComponentProps {
  qr_code_data: string;
}

export const InfoComponent: React.FC<InfoComponentProps> = ({ qr_code_data }) => {
  const navigation = useNavigation();
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchParticipantInfo();
  }, [qr_code_data]);

  const fetchParticipantInfo = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = await AsyncStorage.getItem('access_token');
      const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/api/info/${qr_code_data}`;

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch participant info ${response.statusText}`);
      }

      const responseData = await response.json();
      setData(responseData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error fetching participant info:', err);
    } finally {
      setLoading(false);
    }
  };

  
  const openQRScanner = () => {
    navigation.navigate('qr_scanner' as never, { page: 'info', segment: '' } as never);
  };

  
  const goToHome = () => {
    navigation.navigate('(tabs)' as never);
  };

  const InfoRow = ({ label, value }: { label: string; value: string | number | boolean }) => (
    <View style={tw`flex-row justify-between py-3 border-b border-gray-200`}>
      <Text style={tw`text-textSecondary font-medium`}>{label}:</Text>
      <Text style={tw`text-textPrimary font-semibold`}>{String(value)}</Text>
    </View>
  );

  const StatusBadge = ({ verified }: { verified: boolean }) => (
    <View style={tw`${verified ? 'bg-green-100' : 'bg-red-100'} px-3 py-1 rounded-full`}>
      <Text style={tw`${verified ? 'text-green-700' : 'text-red-700'} font-semibold text-sm`}>
        {verified ? '✓ Verified' : '✗ Not Verified'}
      </Text>
    </View>
  );
  
  const EntryStatusBadge = ({ recorded }: { recorded: boolean }) => (
    <View style={tw`${recorded ? 'bg-green-100' : 'bg-red-100'} px-3 py-1 rounded-full`}>
      <Text style={tw`${recorded ? 'text-green-700' : 'text-red-700'} font-semibold text-sm`}>
        {recorded ? '✓ Recorded' : '✗ Not Recorded'}
      </Text>
    </View>
  );

  const ListSection = ({ title, items }: { title: string; items: string[] }) => {
    if (items.length === 0) return null;
    
    return (
      <View style={tw`mt-4`}>
        <Text style={tw`text-textPrimary font-bold text-base mb-2`}>{title}</Text>
        <View style={tw`bg-white rounded-lg p-3`}>
          {items.map((item, index) => (
            <View key={index} style={tw`flex-row items-center py-1`}>
              <Text style={tw`text-accentLight mr-2`}>•</Text>
              <Text style={tw`text-textPrimary`}>{item}</Text>
            </View>
          ))}
        </View>
      </View>
    );
  };

  const TeamMemberCard = ({ member }: { member: TeamMember }) => (
    <View style={tw`bg-gray-50 rounded-lg p-4 mb-3 border border-gray-200`}>
      <View style={tw`flex-row justify-between items-start mb-2`}>
        <Text style={tw`text-lg font-bold text-textPrimary`}>
          {member.f_name} {member.l_name}
        </Text>
        {member.is_leader && (
          <View style={tw`bg-blue-100 px-2 py-1 rounded-full`}>
            <Text style={tw`text-blue-700 font-semibold text-xs`}>Leader</Text>
          </View>
        )}
      </View>
      <View style={tw`mt-2`}>
        <Text style={tw`text-textSecondary text-sm mb-1`}> {member.email}</Text>
        <Text style={tw`text-textSecondary text-sm mb-1`}> {member.phone}</Text>
        <Text style={tw`text-textSecondary text-sm mb-1`}> Age: {member.age}</Text>
        <Text style={tw`text-textSecondary text-sm mb-1`}> {member.institution}</Text>
        <Text style={tw`text-textSecondary text-sm`}> {member.institution_id}</Text>
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={tw`flex-1 justify-center items-center py-20`}>
        <ActivityIndicator size="large" color="#79BF0D" />
        <Text style={tw`text-textSecondary mt-4`}>Loading participant info...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={tw`flex-1 justify-center items-center py-20`}>
        <Text style={tw`text-red-500 text-center px-4 mb-6`}>{error}</Text>
        <View style={tw`flex-row`}>
          <TouchableOpacity
            style={tw`bg-accentLight px-8 py-3 rounded-lg shadow-sm mr-2`}
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
    );
  }

  if (!data) {
    return (
      <View style={tw`flex-1 justify-center items-center py-20`}>
        <Text style={tw`text-textSecondary text-center px-4`}>No data found</Text>
      </View>
    );
  }

  if (data.participant) {
    const p = data.participant;
    return (
      <View style={tw`pb-6`}>
        <View style={tw`bg-white rounded-xl p-5 mb-4 shadow-sm`}>
          <Text style={tw`text-2xl font-bold text-textPrimary mb-2`}>
            {p.f_name} {p.l_name}
          </Text>
          <View style={tw`flex-row items-center justify-between mt-2`}>
            <Text style={tw`text-textSecondary`}>Participant ID: {p.id}</Text>
            <StatusBadge verified={p.payment_verified} />
          </View>
        </View>

        {/* Personal Information */}
        <View style={tw`bg-white rounded-xl p-5 mb-4 shadow-sm`}>
          <Text style={tw`text-lg font-bold text-textPrimary mb-3`}>Personal Information</Text>
          <InfoRow label="Email" value={p.email} />
          <InfoRow label="Phone" value={p.phone} />
          <InfoRow label="Age" value={p.age} />
          <InfoRow label="Address" value={p.address} />
        </View>


        {/* Institution Information */}
        <View style={tw`bg-white rounded-xl p-5 mb-4 shadow-sm`}>
          <Text style={tw`text-lg font-bold text-textPrimary mb-3`}>Institution</Text>
          <InfoRow label="Name" value={p.institution} />
          <InfoRow label="ID" value={p.institution_id} />
        </View>


        {/* Entry Status */}
        <View style={tw`bg-white rounded-xl p-5 mb-4 shadow-sm`}>
          <View style={tw`flex-row justify-between items-center`}>
            <Text style={tw`text-lg font-bold text-textPrimary`}>Entry Status</Text>
            <EntryStatusBadge recorded={p.entry_status} />
          </View>
        </View>

        {/* Lists */}
        <View style={tw`bg-white rounded-xl p-5 mb-4 shadow-sm`}>
          <ListSection title="Segments" items={p.segment_list} />
          <ListSection title="Competitions" items={p.comp_list} />
          <ListSection title="Gifts" items={p.gift_list} />
        </View>
        

        {/* Action Buttons */}
        <View style={tw`flex-row justify-center mt-4 mb-10`}>
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
    );
  }

  if (data.team) {
    const t = data.team;
    return (
      <View style={tw`pb-6`}>
        <View style={tw`bg-white rounded-xl p-5 mb-4 shadow-sm`}>
          <Text style={tw`text-2xl font-bold text-textPrimary mb-2`}>{t.team_name}</Text>
          <View style={tw`flex-row items-center justify-between mt-2`}>
            <Text style={tw`text-textSecondary`}>Team ID: {t.id}</Text>
            <StatusBadge verified={t.payment_verified} />
          </View>
        </View>

        {/* Entry Status */}
        <View style={tw`bg-white rounded-xl p-5 mb-4 shadow-sm`}>
          <View style={tw`flex-row justify-between items-center`}>
            <Text style={tw`text-lg font-bold text-textPrimary`}>Entry Status</Text>
            <EntryStatusBadge recorded={t.entry_status} />
          </View>
        </View>

        {/* Team Members */}
        {t.members && t.members.length > 0 && (
          <View style={tw`bg-white rounded-xl p-5 mb-4 shadow-sm`}>
            <Text style={tw`text-lg font-bold text-textPrimary mb-3`}>
              Team Members ({t.members.length})
            </Text>
            {t.members.map((member) => (
              <TeamMemberCard key={member.id} member={member} />
            ))}
          </View>
        )}

        {/* Lists */}
        <View style={tw`bg-white rounded-xl p-5 mb-4 shadow-sm`}>
          <ListSection title="Competitions" items={t.comp_list} />
          <ListSection title="Gifts" items={t.gift_list} />
        </View>

        {/* Action Buttons */}
        <View style={tw`flex-row justify-center mt-4`}>
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
    );
  }

  return null;
};