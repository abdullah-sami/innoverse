export type RootStackParamList = {
  Login: undefined;
  '(tabs)': undefined;
  SoloCompetition: undefined;
  TeamCompetition: undefined;
  Segments: undefined;
  qr_scanner: {
    page: string;
    segment?: string | null;
  };
  qr_results_page: {
    page: string;
    segment?: string | null;
    qr_code_data: string;
  };
};

export type TabParamList = {
  index: undefined;
  // Other tab screens
};