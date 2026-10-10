import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../api/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user_info');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('access_token'));
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Validate token and fetch fresh user profile on mount
  useEffect(() => {
    const verifySession = async () => {
      const storedToken = localStorage.getItem('access_token');
      if (storedToken) {
        try {
          const response = await authAPI.getProfile();
          setUser(response.data);
          localStorage.setItem('user_info', JSON.stringify(response.data));
          setToken(storedToken);
        } catch (err) {
          console.warn('Session verification failed, logging out:', err);
          logout();
        }
      } else {
        setUser(null);
        setToken(null);
      }
      setIsLoading(false);
    };

    verifySession();

    // Listen for auth:logout event triggered by axios interceptor
    const handleLogoutEvent = () => logout();
    window.addEventListener('auth:logout', handleLogoutEvent);
    return () => window.removeEventListener('auth:logout', handleLogoutEvent);
  }, []);

  const login = async (username, password) => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const response = await authAPI.login({ username, password });
      const { access, refresh } = response.data;

      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      setToken(access);

      // Fetch user profile immediately with new token
      const profileRes = await authAPI.getProfile();
      setUser(profileRes.data);
      localStorage.setItem('user_info', JSON.stringify(profileRes.data));

      setIsLoading(false);
      return { success: true, user: profileRes.data };
    } catch (err) {
      setIsLoading(false);
      let errorMsg = 'Invalid username or password';
      if (!err.response) {
        errorMsg = 'Cannot connect to the server. Check your connection and try again.';
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.response?.data?.non_field_errors) {
        errorMsg = Array.isArray(err.response.data.non_field_errors)
          ? err.response.data.non_field_errors[0]
          : err.response.data.non_field_errors;
      }
      setAuthError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  const register = async (userData) => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const response = await authAPI.register(userData);
      setIsLoading(false);
      return { success: true, data: response.data };
    } catch (err) {
      setIsLoading(false);
      let errorMsg = 'Registration failed. Please check your inputs.';
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMsg = err.response.data;
        } else if (typeof err.response.data === 'object') {
          const firstKey = Object.keys(err.response.data)[0];
          const val = err.response.data[firstKey];
          errorMsg = Array.isArray(val) ? `${firstKey}: ${val[0]}` : `${firstKey}: ${val}`;
        }
      }
      setAuthError(errorMsg);
      return { success: false, error: errorMsg, errors: err.response?.data };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_info');
    setUser(null);
    setToken(null);
    setAuthError(null);
  };

  const value = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    authError,
    setAuthError,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
