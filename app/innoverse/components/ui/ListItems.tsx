import React from 'react';
import { View, Text, TouchableOpacity, FlatList } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { create } from 'twrnc';
import { ChevronRight } from 'lucide-react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const tw = create(require('../../tailwind.twrnc.config.js'));

interface CompetitionItem {
  id: string;
  title: string;
  navigationRoute?: string;
  onPress?: () => void;
}

interface CompetitionListProps {
  title: string;
  items: CompetitionItem[];
  headerColor?: string;
}

export const CompetitionList: React.FC<CompetitionListProps> = ({ 
  title, 
  items, 
  headerColor = '#79BF0D' 
}) => {
  const navigation = useNavigation();

  const handleItemPress = (item: CompetitionItem) => {
    if (item.onPress) {
      item.onPress();
    } else if (item.navigationRoute) {
        //@ts-ignore
      navigation.navigate(item.navigationRoute as any);
    }
  };

  const renderItem = ({ item}: { item: CompetitionItem}) => (
    <TouchableOpacity
      style={tw`mt-2 mx-4 mb-3 p-4 bg-bgPrimary rounded-xl border border-gray-200 shadow-xl`}
      onPress={() => handleItemPress(item)}
      activeOpacity={0.7}
    >
      <View style={tw`flex-row justify-between items-center`}>
        <Text style={tw`text-textPrimary text-base font-medium flex-1`}>
          {item.title}
        </Text>
        <ChevronRight size={20} color="#79BF0D" />
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={tw`flex-1 bg-bgPrimary`}>
    <View style={tw`flex-1 bg-bgPrimary`}>
      {/* Header */}
      <View 
        style={[
          tw`pt-2 pb-6 px-6`,
          { backgroundColor: headerColor }
        ]}
      >
        <Text style={tw`text-white text-2xl font-bold text-center`}>
          {title}
        </Text>
      </View>

      {/* Content */}
      <View style={tw`flex-1 pt-6`}>
        <FlatList
          data={items}
          renderItem={renderItem}
          keyExtractor={(item) => item.id}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={tw`pb-6`}
        />
      </View>
    </View>
    </SafeAreaView>
  );
};