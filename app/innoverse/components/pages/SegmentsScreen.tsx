import React from 'react';
import { CompetitionList } from '@/components/ui/ListItems';
import { useLogin } from '@/components/context/LoginContextProvider';
import { useNavigation } from '@react-navigation/native';

interface CompetitionItem {
  id: string;
  title: string;
  navigationRoute?: string;
  onPress?: () => void;
}

export const SegmentsScreen: React.FC = () => {
  const { user_id, username } = useLogin();
    const navigation = useNavigation()

    const openQRScanner = (page:string, segment:string) => {
        navigation.navigate('qr_scanner', { page: page, segment: segment});
        };


  const segments: CompetitionItem[] = [
    {
      id: '1',
      title: 'SketchTalk',
      onPress: () => openQRScanner('segment', 'sktech')
    },
    {
      id: '2',
      title: 'PolicyBridge Dialogue',
      onPress: () => openQRScanner('segment', 'policy')
    },
    {
      id: '3',
      title: 'Innovation Expo',
      onPress: () => openQRScanner('segment', 'expo')
    }
  ];

  return (
    <CompetitionList
      title="Segments"
      items={segments}
      headerColor="#79BF0D"
    />
  );
};