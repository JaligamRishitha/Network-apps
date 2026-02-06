/**
 * Authentication Context
 * Requirement 7.1 - Auth context with token management
 *
 * REFACTORED: Now uses authApi instead of direct fetch for consistency
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi, setAuthToken, getAuthToken } from '../services/api';
import logger from '../utils/logger';

interface User {
  username: string;
  roles: string[];
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on mount
    const token = getAuthToken();
    if (token) {
      logger.info('Existing auth token found, restoring session', undefined, 'AUTH');
      // In a real app, validate token and get user info
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
          const userData = JSON.parse(storedUser);
          setUser(userData);
          logger.info('User session restored', { username: userData.username }, 'AUTH');
        } catch (error) {
          logger.error('Failed to parse stored user data', error, 'AUTH');
          localStorage.removeItem('user');
        }
      }
    } else {
      logger.debug('No existing auth token found', undefined, 'AUTH');
    }
    setLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    logger.info('Login attempt started', { username }, 'AUTH');

    try {
      // Use authApi for consistent API handling with interceptors
      const response = await authApi.login(username, password);
      const data = response.data;

      logger.info('Login successful', { username, hasToken: !!data.access_token }, 'AUTH');

      const { access_token } = data;

      setAuthToken(access_token);

      // Store user info (in real app, decode from JWT)
      const userInfo = { username, roles: ['user'] };
      localStorage.setItem('user', JSON.stringify(userInfo));
      setUser(userInfo);

      logger.userAction('User logged in', { username }, 'AUTH');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Login failed';
      logger.error('Login process failed', { error: errorMessage }, 'AUTH');
      throw new Error(errorMessage);
    }
  };

  const logout = () => {
    logger.userAction('User logged out', { username: user?.username }, 'AUTH');
    setAuthToken(null);
    localStorage.removeItem('user');
    setUser(null);
    logger.info('User session cleared', undefined, 'AUTH');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
