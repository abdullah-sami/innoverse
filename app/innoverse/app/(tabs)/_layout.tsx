import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { ImageBackground, Image, View } from 'react-native';

import { icons } from '@/constants/icons';



import HomeScreen from '@/app/(tabs)/index';
import NetworkDashboard from './network';



const Tab = createBottomTabNavigator();



const TabIcon = ({ focused, icon }: { focused: boolean; icon: any }) => {
  if (focused) {
    return (
      <View
        style={{
          backgroundColor: '#79BF0D',
          minWidth: 44,
          width: 44,
          height: 40,
          minHeight: 40,
          justifyContent: 'center',
          alignItems: 'center',
          overflow: 'hidden',
          flex: 1,
          borderBottomLeftRadius: 10, 
          borderBottomRightRadius: 10, 
          elevation: 3,

        }}
      >
        <Image
          source={icon}
          tintColor="#ffffff"
          style={{
            minWidth: 20,
            width: 28,
            height: 28,
            minHeight: 20,
            marginTop: 4,
            position: 'absolute',
            top: 0,
            alignSelf: 'center',
          }}
        />
      </View>
    );
  } else {
    return (
      <View
        style={{
          marginTop: 10,
          minWidth: 48,
          width: 44,
          height: 60,
          minHeight: 48,
          justifyContent: 'center',
          alignItems: 'center',
          overflow: 'hidden',
        }}
      >
        <Image
          source={icon}
          tintColor="#151312"
          style={{
            minWidth: 20,
            width: 32,
            height: 32,
            minHeight: 20,
            marginTop: 4,
          }}
        />
      </View>
    );
  }
};

export default function TabsLayout() {
  return (
    
    <Tab.Navigator
      screenOptions={{
        tabBarShowLabel: false,
        tabBarItemStyle: {
          height: '100%',
          width: '100%',
          borderRadius: 10,
          alignItems: 'center',
          justifyContent: 'center',
        },
        tabBarStyle: {
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 50,
          backgroundColor: '#ffffff',
          borderTopWidth: 0,
          elevation: 0,
        },
      }}
    >
      <Tab.Screen
        component={HomeScreen}
        name="index"
        options={{
          headerShown: false,
          tabBarIcon: ({ focused }) => <TabIcon focused={focused} icon={icons.home} />,
        }}
      />
      {/* <Tab.Screen
        component={NetworkDashboard}
        name="network"
        options={{
          headerShown: false,
          tabBarIcon: ({ focused }) => <TabIcon focused={focused} icon={icons.network} />,
        }}
      /> */}
    </Tab.Navigator>
    
  );
}
