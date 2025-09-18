// components/LoginContextProvider.tsx
import React, { createContext, useContext, useState, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { fetchLogin } from '@/services/api';

interface LoginContextType {
  isLoading: boolean;
  isAuthenticated: boolean;
  user_id: number;
  username: string;
  email: string;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuthStatus: () => Promise<void>;
}

const LoginContext = createContext<LoginContextType | undefined>(undefined);

export const useLogin = () => {
  const context = useContext(LoginContext);
  if (!context) {
    throw new Error('useLogin must be used within a LoginContextProvider');
  }
  return context;
};

interface LoginContextProviderProps {
  children: ReactNode;
}

export const LoginContextProvider: React.FC<LoginContextProviderProps> = ({ children }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user_id, setUser_id] = useState(0);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await fetchLogin({ username, password });

      // Save access token to AsyncStorage
      if (response.access) {
        await AsyncStorage.multiSet([
          ['access_token', response.access], 
          ['refresh_token', response.refresh], 
          ['user_id', response.user.id.toString()], 
          ['username', response.user.username], 
          ['email', response.user.email]
        ]);
        setIsAuthenticated(true);
        setUser_id(response.user.id);
        setEmail(response.user.email);
        setUsername(response.user.username);
      } else {
        throw new Error('No access token received');
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user_id', 'username', 'email']);
      setIsAuthenticated(false);
      setUser_id(0);
      setEmail('');
      setUsername('');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const checkAuthStatus = async () => {
    try {
      // Get all stored values at once
      const values = await AsyncStorage.multiGet([
        'access_token', 
        'user_id', 
        'username', 
        'email'
      ]);

      const token = values[0][1]; // access_token
      const storedUserId = values[1][1]; // user_id
      const storedUsername = values[2][1]; // username
      const storedEmail = values[3][1]; // email

      if (token) {
        setIsAuthenticated(true);
        // Restore user data from AsyncStorage
        if (storedUserId) setUser_id(parseInt(storedUserId));
        if (storedUsername) setUsername(storedUsername);
        if (storedEmail) setEmail(storedEmail);
      } else {
        setIsAuthenticated(false);
        // Clear state if no token
        setUser_id(0);
        setUsername('');
        setEmail('');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
      setUser_id(0);
      setUsername('');
      setEmail('');
    }
  };

  const value: LoginContextType = {
    isLoading,
    isAuthenticated,
    user_id,
    username,
    email,
    login,
    logout,
    checkAuthStatus,
  };

  return (
    <LoginContext.Provider value={value}>
      {children}
    </LoginContext.Provider>
  );
};