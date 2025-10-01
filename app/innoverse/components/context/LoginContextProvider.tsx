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

const refreshAccessToken = async () => {
  const refresh = await AsyncStorage.getItem("refresh_token");
  if (!refresh) {
    throw new Error("Refresh token not found. Please log in again.");
  }

  const response = await fetch(
    `${INNOVERSE_API_CONFIG.BASE_URL}/auth/token/refresh`,
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

      if (response.access) {
        await AsyncStorage.multiSet([
          ['access_token', response.access], 
          ['refresh_token', response.refresh], 
          ['user_id', response.user.id.toString()], 
          ['username', response.user.username], 
          ['email', response.user.email],
          ['last_token_validation', Date.now().toString()] 
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

      const response = await fetch(`${INNOVERSE_API_CONFIG.BASE_URL}/api/gifts/p_01`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        try {
          console.log('Access token expired, attempting to refresh...');
          await refreshAccessToken();
          await AsyncStorage.setItem('last_token_validation', Date.now().toString());
          return true;
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError);
          await logout();
          return false;
        }
      } else if (response.ok) {
        await AsyncStorage.setItem('last_token_validation', Date.now().toString());
        return true;
      } else {
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
        return true; 
      }

      const lastValidationTime = parseInt(lastValidation);
      const oneDayInMs = 24 * 60 * 60 * 1000; // 24 hours
      const now = Date.now();

      return (now - lastValidationTime) > oneDayInMs;
    } catch (error) {
      console.error('Error checking validation timestamp:', error);
      return true; 
  };
  }
  const checkAuthStatus = async () => {
    setIsLoading(true);
    try {
      const values = await AsyncStorage.multiGet([
        'access_token', 
        'user_id', 
        'username', 
        'email'
      ]);

      const token = values[0][1]; 
      const storedUserId = values[1][1]; 
      const storedUsername = values[2][1]; 
      const storedEmail = values[3][1]; 

      if (!token) {
        setIsAuthenticated(false);
        setUser_id(0);
        setUsername('');
        setEmail('');
        setIsLoading(false);
        return;
      }

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

      setIsAuthenticated(true);
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