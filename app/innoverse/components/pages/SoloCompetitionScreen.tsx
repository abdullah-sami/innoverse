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

export const SoloCompetitionScreen: React.FC = () => {
  const { user_id, username } = useLogin();

  const navigation = useNavigation()

    const openQRScanner = (page:string, segment:string) => {
        navigation.navigate('qr_scanner', { page: page, segment: segment});
        };

  const soloCompetitions: CompetitionItem[] = [
    {
      id: '1',
      title: 'Programming Contest',
      onPress: () => openQRScanner('solo', 'programming')
    },
    {
      id: '12',
      title: 'Math Auction',
      onPress: () => openQRScanner('solo', 'm_auction')
    },
    {
      id: '3',
      title: 'Science Olympiad',
      onPress: () => openQRScanner('solo', 'sc_olym')
    },
    {
      id: '4',
      title: 'Research Abstract',      
      onPress: () => openQRScanner('solo', 'res_abs')
    },
    {
      id: '5',
      title: '3-Minute Research',
      onPress: () => openQRScanner('solo', '3m-res')
    }
  ];

  return (
    <CompetitionList
      title="Solo Competitions"
      items={soloCompetitions}
      headerColor="#79BF0D"
    />
  );
};