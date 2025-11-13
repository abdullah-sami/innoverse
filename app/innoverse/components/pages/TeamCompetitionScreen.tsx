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

export const TeamCompetitionScreen: React.FC = () => {
  const { user_id, username } = useLogin();

  const navigation = useNavigation()

  const openQRScanner = (page:string, segment:string) => {
        navigation.navigate('qr_scanner', { page: page, segment: segment});
        };


  const teamCompetitions: CompetitionItem[] = [
        {
      id: '1',
      title: 'RoboSoccer',
      onPress: () => openQRScanner('team', 'robo_soccer')
    },
    {
      id: '2',
      title: 'Qwizard Mania',
      onPress: () => openQRScanner('team', 'q_mania')
    },
    {
      id: '3',
      title: 'Project Showcasing',
      onPress: () => openQRScanner('team', 'pr_show')
    },
    {
      id: '4',
      title: 'Line Forwarding Robot',
      onPress: () => openQRScanner('team', 'lfr')
    }
  ];

  return (
    <CompetitionList
      title="Team Competitions"
      items={teamCompetitions}
      headerColor="#79BF0D"
    />
  );
};