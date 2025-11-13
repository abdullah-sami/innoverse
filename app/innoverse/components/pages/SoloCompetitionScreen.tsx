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
      title: 'Math Maestro',
      onPress: () => openQRScanner('solo', 'math_maestro')
    },
    {
      id: '12',
      title: 'Research Article Contest',
      onPress: () => openQRScanner('solo', 'r_article')
    },
    {
      id: '3',
      title: 'Programming Contest',
      onPress: () => openQRScanner('solo', 'programming')
    },
    {
      id: '4',
      title: 'Science Olympiad',      
      onPress: () => openQRScanner('solo', 'sc_olym')
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