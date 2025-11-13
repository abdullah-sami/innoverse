import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  Alert, 
  StyleSheet, 
  Dimensions, 
  TouchableOpacity,
  StatusBar 
} from 'react-native';
import { CameraView, Camera } from 'expo-camera';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { create } from 'twrnc'

const tw = create(require('../../tailwind.twrnc.config.js'));

const { width, height } = Dimensions.get('window');
const scanAreaSize = width * 0.7;

export const QRScanner: React.FC = () => {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [scanned, setScanned] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigation = useNavigation();
  const route = useRoute();
  
  const { page, segment = null } = route.params as { page: string; segment?: string | null };

  // console.log('QR Scanner - Page:', page, 'Segment:', segment);

  useEffect(() => {
    getCameraPermissions();
  }, []);

  const getCameraPermissions = async () => {
    try {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
      setIsLoading(false);
    } catch (error) {
      console.error('Error requesting camera permission:', error);
      setHasPermission(false);
      setIsLoading(false);
    }
  };

  const handleBarCodeScanned = ({ type, data }: { type: string; data: string }) => {
    if (scanned) return;
    
    setScanned(true);
    
    
    navigation.navigate('qr_results_page' as never, { 
      page, 
      segment, 
      qr_code_data: data 
    } as never);
  };

  const resetScanner = () => {
    setScanned(false);
  };

  const handlePermissionDenied = () => {
    Alert.alert(
      'Camera Permission Required',
      'This app needs camera permission to scan QR codes. Please enable camera access in your device settings.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Retry', 
          onPress: getCameraPermissions 
        }
      ]
    );
  };

  if (isLoading) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading camera...</Text>
        </View>
      </View>
    );
  }

  if (hasPermission === null) {
    return (
      <View style={styles.container}>
        <View style={styles.permissionContainer}>
          <Text style={styles.permissionText}>Requesting camera permission...</Text>
        </View>
      </View>
    );
  }

  if (hasPermission === false) {
    return (
      <View style={styles.container}>
        <View style={styles.permissionContainer}>
          <Ionicons name="camera-outline" size={64} color="#7D7D7D" />
          <Text style={styles.permissionText}>Camera permission denied</Text>
          <Text style={styles.permissionSubtext}>
            We need camera access to scan QR codes
          </Text>
          <TouchableOpacity style={styles.retryButton} onPress={handlePermissionDenied}>
            <Text style={styles.retryButtonText}>Grant Permission</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <SafeAreaView style={tw`flex-1 bg-bgPrimary`}>
      <StatusBar backgroundColor="#79BF0D" barStyle="light-content" />
      
      <View style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#000" />
        
        <CameraView
          style={styles.camera}
          facing="back"
          onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
          barcodeScannerSettings={{
            barcodeTypes: ['qr', 'pdf417', 'aztec', 'ean13', 'ean8', 'upc_e', 'code128', 'code39'],
          }}
        >
          {/* Camera overlay */}
          <View style={styles.overlay}>
            {/* Top overlay */}
            <View style={styles.overlayTop} />
            
            {/* Middle section with scan area */}
            <View style={styles.overlayMiddle}>
              <View style={styles.overlaySide} />
              <View style={styles.scanArea}>
                {/* Corner indicators */}
                <View style={[styles.corner, styles.topLeft]} />
                <View style={[styles.corner, styles.topRight]} />
                <View style={[styles.corner, styles.bottomLeft]} />
                <View style={[styles.corner, styles.bottomRight]} />
              </View>
              <View style={styles.overlaySide} />
            </View>
            
            {/* Bottom overlay */}
            <View style={styles.overlayBottom}>
              <Text style={styles.instructionText}>
                Put QR Code inside the rectangle
              </Text>
              
              {scanned && (
                <TouchableOpacity style={styles.rescanButton} onPress={resetScanner}>
                  <Text style={styles.rescanButtonText}>Tap to Scan Again</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        </CameraView>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  overlayTop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  overlayMiddle: {
    flexDirection: 'row',
    height: scanAreaSize,
  },
  overlaySide: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  scanArea: {
    width: scanAreaSize,
    height: scanAreaSize,
    position: 'relative',
    borderRadius: 20,
    overflow: 'hidden',
  },
  corner: {
    position: 'absolute',
    width: 30,
    height: 30,
    borderColor: '#79BF0D',
    borderWidth: 4,
  },
  topLeft: {
    top: 10,
    left: 10,
    borderBottomWidth: 0,
    borderRightWidth: 0,
    borderTopLeftRadius: 10,
  },
  topRight: {
    top: 10,
    right: 10,
    borderBottomWidth: 0,
    borderLeftWidth: 0,
    borderTopRightRadius: 10,
  },
  bottomLeft: {
    bottom: 10,
    left: 10,
    borderTopWidth: 0,
    borderRightWidth: 0,
    borderBottomLeftRadius: 10,
  },
  bottomRight: {
    bottom: 10,
    right: 10,
    borderTopWidth: 0,
    borderLeftWidth: 0,
    borderBottomRightRadius: 10,
  },
  overlayBottom: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  instructionText: {
    color: '#ffffff',
    fontSize: 16,
    textAlign: 'center',
    marginTop: 30,
    fontWeight: '500',
  },
  rescanButton: {
    backgroundColor: '#79BF0D',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 25,
    marginTop: 20,
  },
  rescanButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F4FFE2',
  },
  loadingText: {
    color: '#2e2e2e',
    fontSize: 16,
    fontWeight: '500',
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F4FFE2',
    paddingHorizontal: 20,
  },
  permissionText: {
    color: '#2e2e2e',
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: 20,
  },
  permissionSubtext: {
    color: '#7D7D7D',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 10,
    marginBottom: 30,
  },
  retryButton: {
    backgroundColor: '#1A8249',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 25,
  },
  retryButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});