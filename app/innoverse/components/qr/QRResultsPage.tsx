import React from 'react';
import { View, Text, TouchableOpacity, StatusBar } from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { create } from 'twrnc'

const tw = create(require('../../tailwind.twrnc.config.js'));

export const QRResultsPage = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const { page, segment, qr_code_data } = route.params;

  return (
    <SafeAreaView style={tw`flex-1 bg-bgPrimary`}>
    <StatusBar backgroundColor="#79BF0D" barStyle="light-content" />
    

    <View style={{ flex: 1, padding: 20 }}>
      <Text>QR Code Data: {qr_code_data}</Text>
      <Text>From Page: {page}</Text>
      <Text>Segment: {segment || 'None'}</Text>
      
      <TouchableOpacity onPress={() => navigation.goBack()}>
        <Text>Go Back</Text>
      </TouchableOpacity>
    </View>
    </SafeAreaView>

  );
};