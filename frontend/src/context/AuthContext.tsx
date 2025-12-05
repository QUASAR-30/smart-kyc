import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '../api/axios';
import { IMerchant } from '../types';

interface AuthContextType {
  isAuthenticated: boolean;
  user: IMerchant | null;
  login: (email: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<IMerchant | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Check if user is already logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const response = await api.get('/auth/me');
          setUser(response.data);
          setIsAuthenticated(true);
        } catch (error) {
          // Token invalid or expired
          localStorage.removeItem('access_token');
          setIsAuthenticated(false);
          setUser(null);
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string) => {
    try {
      const response = await api.post('/auth/mock-login', { email });
      const { access_token, merchant } = response.data;

      // Store token
      localStorage.setItem('access_token', access_token);

      // Update state
      setUser(merchant);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        user,
        login,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
