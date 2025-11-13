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
  ActivityIndicator,
  Keyboard,
  TouchableWithoutFeedback,
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
  const [errorMessage, setErrorMessage] = useState('');
  const { login, isLoading } = useLogin();
  const navigation = useNavigation();
  
  const passwordRef = useRef<TextInput>(null);
  const scrollViewRef = useRef<ScrollView>(null);

  const handleLogin = async () => {
    // Dismiss keyboard
    Keyboard.dismiss();
    
    // Clear previous error
    setErrorMessage('');

    // Validation
    if (!username.trim() || !password.trim()) {
      setErrorMessage('Please enter both username and password');
      return;
    }

    try {
      await login(username, password);
      navigation.navigate('(tabs)' as never);
    } catch (error: any) {
      console.error('Login error:', error);
      
      // Determine error type and show appropriate message
      let errorMsg = 'An unexpected error occurred. Please try again.';
      
      if (error.message) {
        if (error.message.includes('Network request failed') || 
            error.message.includes('fetch') ||
            error.message.includes('network')) {
          errorMsg = 'Network error. Please check your internet connection and try again.';
        } else if (error.message.includes('Failed to login') || 
                   error.message.includes('401') ||
                   error.message.includes('Invalid')) {
          errorMsg = 'Invalid username or password. Please try again.';
        } else if (error.message.includes('timeout')) {
          errorMsg = 'Connection timeout. Please try again.';
        } else if (error.message.includes('500') || error.message.includes('Server')) {
          errorMsg = 'Server error. Please try again later.';
        } else {
          errorMsg = error.message;
        }
      }
      
      setErrorMessage(errorMsg);
      
      // Also show alert for critical errors
      if (errorMsg.includes('Network') || errorMsg.includes('Server')) {
        Alert.alert('Connection Error', errorMsg);
      }
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <SafeAreaView style={tw`flex-1 bg-bgPrimary`} edges={['top']}>
      <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
        <KeyboardAvoidingView 
          style={tw`flex-1`} 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={0}
        >
          <ScrollView 
            ref={scrollViewRef}
            style={tw`flex-1 bg-bgPrimary`}
            contentContainerStyle={tw`flex-grow`}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
            bounces={false}
          >
            {/* Logo Section - Takes available space */}
            <View style={tw`flex-1 justify-center items-center px-6 py-8`}>
              <Image
                source={images.logo}
                style={tw`w-64 h-64`}
                resizeMode="contain"
              />
            </View>

            {/* Login Form Section - Fixed at bottom */}
            <View 
              style={tw`px-6 pt-8 pb-8 rounded-t-3xl bg-accentLight`}
            >
              <Text style={tw`text-white text-3xl font-bold mb-6`}>
                WELCOME!
              </Text>

              {/* Error Message Banner */}
              {errorMessage ? (
                <View style={tw`bg-red-500 rounded-lg p-4 mb-4 flex-row items-start`}>
                  <Ionicons 
                    name="alert-circle" 
                    size={20} 
                    style={tw`text-white mr-2 mt-0.5`} 
                  />
                  <Text style={tw`text-white flex-1 text-sm leading-5`}>
                    {errorMessage}
                  </Text>
                </View>
              ) : null}

              <View style={tw`mb-4`}>
                <View style={tw`flex-row items-center bg-white rounded-lg px-4 py-3 ${
                  errorMessage && !username.trim() ? 'border-2 border-red-300' : ''
                }`}>
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
                    onChangeText={(text) => {
                      setUsername(text);
                      setErrorMessage('');
                    }}
                    onFocus={() => {
                      // Scroll to bottom when focused
                      setTimeout(() => {
                        scrollViewRef.current?.scrollToEnd({ animated: true });
                      }, 100);
                    }}
                    autoCapitalize="none"
                    autoCorrect={false}
                    returnKeyType="next"
                    onSubmitEditing={() => passwordRef.current?.focus()}
                    blurOnSubmit={false}
                    editable={!isLoading}
                  />
                </View>
              </View>

              <View style={tw`mb-6`}>
                <View style={tw`flex-row items-center bg-white rounded-lg px-4 py-3 ${
                  errorMessage && !password.trim() ? 'border-2 border-red-300' : ''
                }`}>
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
                    onChangeText={(text) => {
                      setPassword(text);
                      setErrorMessage('');
                    }}
                    onFocus={() => {
                      // Scroll to bottom when focused
                      setTimeout(() => {
                        scrollViewRef.current?.scrollToEnd({ animated: true });
                      }, 100);
                    }}
                    secureTextEntry={!showPassword}
                    autoCapitalize="none"
                    autoCorrect={false}
                    returnKeyType="done"
                    onSubmitEditing={handleLogin}
                    editable={!isLoading}
                  />
                  <TouchableOpacity
                    onPress={togglePasswordVisibility}
                    style={tw`ml-2 p-1`}
                    disabled={isLoading}
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
                  tw`bg-white py-4 rounded-lg mb-6 flex-row justify-center items-center`,
                  isLoading && tw`opacity-70`
                ]}
                onPress={handleLogin}
                disabled={isLoading}
              >
                {isLoading && (
                  <ActivityIndicator 
                    size="small" 
                    color="#79BF0D" 
                    style={tw`mr-2`}
                  />
                )}
                <Text style={tw`text-center font-bold text-lg text-accentLight`}>
                  {isLoading ? 'LOGGING IN...' : 'LOGIN'}
                </Text>
              </TouchableOpacity>

              <Text style={tw`text-white text-center text-sm opacity-90`}>
                If You Don't Have An Account,{'\n'}Ask Your Admin For One.
              </Text>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </TouchableWithoutFeedback>
    </SafeAreaView>
  );
};