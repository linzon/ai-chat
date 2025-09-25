import { useState, useEffect } from 'react';
import { apiClient, type User } from '../api/client';

interface AuthState {
  user: User | null;
  loading: boolean;
}

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    loading: true
  });

  useEffect(() => {
    // Check if user is already logged in
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        setAuthState({
          user,
          loading: false
        });
      } catch (e) {
        // If parsing fails, remove invalid data
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        setAuthState({
          user: null,
          loading: false
        });
      }
    } else {
      setAuthState({
        user: null,
        loading: false
      });
    }
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.login(email, password);
      setAuthState({
        user: response.user,
        loading: false
      });
      return response.user;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const register = async (username: string, email: string, phone: string, password: string) => {
    try {
      const user = await apiClient.register(username, email, phone, password);
      setAuthState({
        user,
        loading: false
      });
      return user;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const logout = () => {
    apiClient.logout();
    setAuthState({
      user: null,
      loading: false
    });
  };

  return {
    user: authState.user,
    loading: authState.loading,
    login,
    register,
    logout
  };
}