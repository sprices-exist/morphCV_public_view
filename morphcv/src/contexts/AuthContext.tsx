import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import authService, { UserProfile } from '../lib/api/authService';

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (token: string, userInfo: any) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Check if user is already authenticated
  useEffect(() => {
    const checkAuth = async () => {
      const accessToken = localStorage.getItem('access_token');
      
      if (accessToken) {
        try {
          const { user } = await authService.getCurrentUser();
          setUser(user);
        } catch (err) {
          console.error('Authentication error:', err);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }
      
      setIsLoading(false);
    };
    
    checkAuth();
  }, []);
  
  const login = async (token: string, userInfo: any) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Call Google OAuth login endpoint
      const response = await authService.googleLogin({
        token,
        user_info: userInfo
      });
      
      // Store tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      
      // Set user
      setUser(response.user);
    } catch (err) {
      console.error('Login error:', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  const logout = async () => {
    setIsLoading(true);
    
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (refreshToken) {
        await authService.logout(refreshToken);
      }
      
      // Clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      // Clear user
      setUser(null);
    } catch (err) {
      console.error('Logout error:', err);
      
      // Even if the API call fails, we still want to clear the local state
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };
  
  const refreshUser = async () => {
    if (!localStorage.getItem('access_token')) {
      return;
    }
    
    try {
      const { user } = await authService.getCurrentUser();
      setUser(user);
    } catch (err) {
      console.error('Error refreshing user:', err);
      
      // If unauthorized, clear tokens and user
      if (err instanceof Error && err.message.includes('Authentication error')) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
      }
    }
  };
  
  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    logout,
    refreshUser
  };
  
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};