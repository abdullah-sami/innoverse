import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Image,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { create } from 'twrnc';
import { images } from '@/constants/images';
import { useLogin } from '../context/LoginContextProvider';
import { useNavigation } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';

const tw = create(require('../../tailwind.twrnc.config.js'));

export const LoginScreen = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { login, isLoading } = useLogin();
  const navigation = useNavigation();
  
  const passwordRef = useRef<TextInput>(null);

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert('Error', 'Please enter both username and password');
      return;
    }

    try {
      await login(username, password);
      navigation.navigate('(tabs)' as never);
    } catch (error) {
      Alert.alert('Login Failed', 'Invalid username or password. Please try again.');
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <SafeAreaView style={tw`flex-1 bg-bgPrimary`}>
      <KeyboardAvoidingView 
        style={tw`flex-1`} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        <ScrollView 
          style={tw`flex-1 bg-bgPrimary`}
          contentContainerStyle={tw`flex-grow justify-between`}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <View style={tw`flex-1 justify-center items-center px-6 pt-16 min-h-96`}>
            <View style={tw`items-center mb-6`}>
              <Image
                source={images.logo}
                style={tw`w-80 h-80`}
                resizeMode="contain"
              />
            </View>
          </View>

          <View 
            style={tw`px-6 pt-8 pb-12 rounded-t-3xl bg-accentLight`}
          >
            <Text style={tw`text-white text-3xl font-bold mb-8`}>
              WELCOME!
            </Text>

            <View style={tw`mb-4`}>
              <View style={tw`flex-row items-center bg-white rounded-lg px-4 py-3`}>
                <Ionicons 
                  name="person-outline" 
                  size={20} 
                  style={tw`mr-3 text-textSecondary`} 
                />
                <TextInput
                  style={tw`flex-1 text-base text-textPrimary`}
                  placeholder="username"
                  placeholderTextColor={'#7D7D7D'}
                  value={username}
                  onChangeText={setUsername}
                  autoCapitalize="none"
                  autoCorrect={false}
                  returnKeyType="next"
                  onSubmitEditing={() => passwordRef.current?.focus()}
                  blurOnSubmit={false}
                />
              </View>
            </View>

            <View style={tw`mb-6`}>
              <View style={tw`flex-row items-center bg-white rounded-lg px-4 py-3`}>
                <Ionicons 
                  name="lock-closed-outline" 
                  size={20} 
                  style={tw`mr-3 text-textSecondary`} 
                />
                <TextInput
                  ref={passwordRef}
                  style={tw`flex-1 text-base text-textPrimary`}
                  placeholder="password"
                  placeholderTextColor={'#7D7D7D'}
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry={!showPassword}
                  autoCapitalize="none"
                  autoCorrect={false}
                  returnKeyType="done"
                  onSubmitEditing={handleLogin}
                />
                <TouchableOpacity
                  onPress={togglePasswordVisibility}
                  style={tw`ml-2 p-1`}
                >
                  <Ionicons 
                    name={showPassword ? "eye-off-outline" : "eye-outline"} 
                    size={20} 
                    style={tw`text-textSecondary`} 
                  />
                </TouchableOpacity>
              </View>
            </View>

            <TouchableOpacity
              style={[
                tw`bg-white py-4 rounded-lg mb-6`,
                isLoading && tw`opacity-70`
              ]}
              onPress={handleLogin}
              disabled={isLoading}
            >
              <Text style={tw`text-center font-bold text-lg text-accentLight`}>
                {isLoading ? 'LOGGING IN...' : 'LOGIN'}
              </Text>
            </TouchableOpacity>

            <Text style={tw`text-white text-center text-sm`}>
              If You Don't Have An Account,{'\n'}Ask Your Admin For One.
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};