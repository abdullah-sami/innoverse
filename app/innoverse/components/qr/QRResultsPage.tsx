import React from 'react';
import { View, Text, TouchableOpacity, StatusBar, ScrollView } from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { create } from 'twrnc';
import { EntryResultComponent } from './EntryResultComponent';
import { GiftsResultComponent } from './GiftsResultComponent';
import { GenericResultComponent } from './GenericResultComponent';
import { InfoComponent } from './InfoComponent';

const tw = create(require('../../tailwind.twrnc.config.js'));

interface RouteParams {
  page: string;
  segment: string;
  qr_code_data: string;
}

export const QRResultsPage = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const { page, segment, qr_code_data } = route.params as RouteParams;

  const getPageTitle = () => {
    if (page === 'entry') return 'Record Entry';
    if (page === 'gifts') return 'Gifts';
    return page.charAt(0).toUpperCase() + page.slice(1);
  };

  const handleBack = () => {
    navigation.reset({
      index: 0,
      routes: [{ name: 'index' }],
    });
  };

  const renderResultComponent = () => {
    switch (page) {
      case 'entry':
        return <EntryResultComponent qr_code_data={qr_code_data} />;
      case 'gifts':
        return <GiftsResultComponent qr_code_data={qr_code_data} />;
      case 'info':
        return <InfoComponent qr_code_data={qr_code_data} />;
      default:
        return (
          <GenericResultComponent 
            page={page} 
            segment={segment} 
            qr_code_data={qr_code_data} 
          />
        );
    }
  };

  return (
    <SafeAreaView style={tw`flex-1 bg-bgPrimary`}>
      <StatusBar backgroundColor="#79BF0D" barStyle="light-content" />
      
      
      <View style={tw`bg-accentLight px-4 py-3 flex-row items-center`}>
        <Text style={tw`text-white text-lg font-semibold ml-5`}>{getPageTitle()}</Text>
      </View>

      <ScrollView style={tw`flex-1 px-4 pt-6`}>
        {renderResultComponent()}
      </ScrollView>
    </SafeAreaView>
  );
};