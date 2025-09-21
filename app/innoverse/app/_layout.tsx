// _layout.tsx (root)
import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { RootStackParamList } from '@/types/navigation';
import './globals.css';

import { LoginContextProvider, useLogin } from '@/components/context/LoginContextProvider';
import { LoginScreen } from '@/components/auth/LoginScreen';
import { QRScanner } from '@/components/qr/QRScanner';
import { QRResultsPage } from '@/components/qr/QRResultsPage';
import TabLayout from './(tabs)/_layout';
import { SoloCompetitionScreen } from '@/components/pages/SoloCompetitionScreen';
import { TeamCompetitionScreen } from '@/components/pages/TeamCompetitionScreen';
import { SegmentsScreen } from '@/components/pages/SegmentsScreen';

const Stack = createNativeStackNavigator<RootStackParamList>();

export const linking = {
  prefixes: ['innoverse://', 'https://innoverse.com'],
  config: {
    screens: {
      Login: 'login',
      '(tabs)': '',
    },
  },
};




function AppNavigator() {
  const { isAuthenticated, checkAuthStatus } = useLogin();

  useEffect(() => {
    checkAuthStatus();
  }, []);

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isAuthenticated ? (<>
        <Stack.Screen name="(tabs)" component={TabLayout} /> 
        <Stack.Screen name="SoloCompetition" component={SoloCompetitionScreen} /> 
        <Stack.Screen name="TeamCompetition" component={TeamCompetitionScreen} /> 
        <Stack.Screen name="Segments" component={SegmentsScreen} /> 
        
        
        
        <Stack.Screen name="qr_scanner" component={QRScanner} options={{ presentation: 'modal'}}/>
        <Stack.Screen name="qr_results_page" component={QRResultsPage}/>

</>
        
      ) : (
        <Stack.Screen name="Login" component={LoginScreen} />
      )}
    </Stack.Navigator>
  );
}

export default function RootLayout() {
  return (
    <LoginContextProvider>
      {/* <NavigationContainer linking={linking}> */}
        <AppNavigator />
      {/* </NavigationContainer> */}
    </LoginContextProvider>
  );
}