// components/context/LoginContextProvider.tsx
import React, { createContext, useContext, useState, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { fetchLogin, INNOVERSE_API_CONFIG } from '@/services/api';

interface LoginContextType {
  isLoading: boolean;
  isAuthenticated: boolean;
  user_id: number;
  username: string;
  email: string;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuthStatus: () => Promise<void>;
  validateToken: () => Promise<boolean>;
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

// Helper function to refresh the access token
const refreshAccessToken = async () => {
  const refresh = await AsyncStorage.getItem("refresh_token");
  if (!refresh) {
    throw new Error("Refresh token not found. Please log in again.");
  }

  const response = await fetch(
    `${INNOVERSE_API_CONFIG.BASE_URL}/api/token/refresh/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh }),
    }
  );

  if (!response.ok) {
    await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user_id', 'username', 'email']);
    throw new Error("Session expired. Please log in again.");
  }

  const data = await response.json();
  await AsyncStorage.setItem("access_token", data.access);
  return data.access;
};

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
          ['email', response.user.email],
          ['last_token_validation', Date.now().toString()] // Store validation timestamp
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
      await AsyncStorage.multiRemove([
        'access_token', 
        'refresh_token', 
        'user_id', 
        'username', 
        'email',
        'last_token_validation'
      ]);
      setIsAuthenticated(false);
      setUser_id(0);
      setEmail('');
      setUsername('');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const validateToken = async (): Promise<boolean> => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        return false;
      }

      // Test token validity by making a request to /api/reels/
      const response = await fetch(`${INNOVERSE_API_CONFIG.BASE_URL}/api/reels/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        // Token is invalid, try to refresh
        try {
          console.log('Access token expired, attempting to refresh...');
          await refreshAccessToken();
          await AsyncStorage.setItem('last_token_validation', Date.now().toString());
          return true;
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError);
          // Clear all auth data if refresh fails
          await logout();
          return false;
        }
      } else if (response.ok) {
        // Token is valid
        await AsyncStorage.setItem('last_token_validation', Date.now().toString());
        return true;
      } else {
        // Other error, assume token is invalid
        console.error('Token validation failed with status:', response.status);
        return false;
      }
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
  };

  const shouldValidateToken = async (): Promise<boolean> => {
    try {
      const lastValidation = await AsyncStorage.getItem('last_token_validation');
      if (!lastValidation) {
        return true; // Never validated before
      }

      const lastValidationTime = parseInt(lastValidation);
      const oneDayInMs = 24 * 60 * 60 * 1000; // 24 hours
      const now = Date.now();

      return (now - lastValidationTime) > oneDayInMs;
    } catch (error) {
      console.error('Error checking validation timestamp:', error);
      return true; // Default to validating if there's an error
    }
  };

  const checkAuthStatus = async () => {
    setIsLoading(true);
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

      if (!token) {
        setIsAuthenticated(false);
        setUser_id(0);
        setUsername('');
        setEmail('');
        setIsLoading(false);
        return;
      }

      // Check if we should validate the token (once per day)
      const needsValidation = await shouldValidateToken();
      
      if (needsValidation) {
        console.log('Validating token...');
        const isValid = await validateToken();
        
        if (!isValid) {
          setIsAuthenticated(false);
          setUser_id(0);
          setUsername('');
          setEmail('');
          setIsLoading(false);
          return;
        }
      }

      // Token exists and is valid (or validation not needed yet)
      setIsAuthenticated(true);
      // Restore user data from AsyncStorage
      if (storedUserId) setUser_id(parseInt(storedUserId));
      if (storedUsername) setUsername(storedUsername);
      if (storedEmail) setEmail(storedEmail);

    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
      setUser_id(0);
      setUsername('');
      setEmail('');
    } finally {
      setIsLoading(false);
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
    validateToken,
  };

  return (
    <LoginContext.Provider value={value}>
      {children}
    </LoginContext.Provider>
  );
};