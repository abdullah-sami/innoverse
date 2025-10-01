import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Image,
  StatusBar,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useLogin } from '@/components/context/LoginContextProvider';
import { images } from '@/constants/images';
import { create } from 'twrnc';
import { SafeAreaView } from 'react-native-safe-area-context';
const tw = create(require('../../tailwind.twrnc.config.js'));

const HomeScreen = () => {
  const navigation = useNavigation();
  const { username, logout } = useLogin();

  const openQRScanner = (page:string, segment:string) => {
    console.log(page)
  navigation.navigate('qr_scanner', { page: page, segment: segment});
};

  const menuItems = [
    {
      id: 1,
      title: 'Record Entry',
      image: images.entry,
      onPress: () => openQRScanner('entry', 'entry'),
    },
    {
      id: 2,
      title: 'Segments',
      image: images.segments,
      onPress: () => navigation.navigate('Segments' as never),
    },
    {
      id: 3,
      title: 'Team',
      image: images.team_comp,
      onPress: () => navigation.navigate('Team' as never),
    },
    {
      id: 4,
      title: 'Solo',
      image: images.solo_comp,
      onPress: () => navigation.navigate('Solo' as never),
    },
    {
      id: 5,
      title: 'Gifts',
      image: images.gifts,
      onPress: () => openQRScanner('gifts', ''),
    },
    {
      id: 6,
      title: 'View Info',
      image: images.participant_info,
      onPress: () => openQRScanner('info', ''),
    },
  ];

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const renderMenuItem = (item: typeof menuItems[0]) => (
    <TouchableOpacity
      key={item.id}
      style={tw`w-[47%] mb-5`}
      onPress={item.onPress}
      activeOpacity={0.7}
    >
      <View style={tw`bg-white rounded-2xl p-5 items-center shadow-sm min-h-[120px] justify-center`}>
        <View style={tw`w-12 h-12 justify-center items-center mb-3`}>
          <Image 
            source={item.image} 
            style={[tw`w-12 h-12`]} 
            resizeMode="contain" 
          />
        </View>
        <Text style={tw`text-sm font-semibold text-textPrimary text-center`}>
          {item.title}
        </Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={tw`flex-1 bg-bgPrimary`}>
      <StatusBar backgroundColor="#79BF0D" barStyle="light-content" />
      
      <View style={tw`flex-row justify-between items-center bg-accentLight px-5 py-4 shadow-md`}>
        <View style={tw`flex-row items-center`}>
          <View style={tw`w-10 h-10 bg-white rounded-full justify-center items-center mr-3`}>
            <Image source={images.logo_main} style={tw`w-9 h-9`} resizeMode="contain" />
          </View>
          <Text style={tw`text-white text-lg font-semibold`}>
            Hello, {username}!
          </Text>
        </View>
        
        <TouchableOpacity
          style={tw`flex-row items-center bg-white bg-opacity-20 px-3 py-2 rounded-full border border-white border-opacity-30`}
          onPress={handleLogout}
          activeOpacity={0.7}
        >
          <Text style={tw`text-white text-xs font-semibold mr-1.5`}>LOGOUT</Text>
          <Image 
            source={images.logout} 
            style={[tw`w-4 h-4`, { tintColor: '#ffffff' }]} 
            resizeMode="contain" 
          />
        </TouchableOpacity>
      </View>

      {/* Menu Grid */}
      <View style={tw`flex-1 px-5 pt-15`}>
        <View style={tw`flex-row flex-wrap justify-between`}>
          {menuItems.map(renderMenuItem)}
        </View>
      </View>
    </SafeAreaView>
  );
};

export default HomeScreen;